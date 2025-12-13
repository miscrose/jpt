import os
import uvicorn
import requests
from fastapi import FastAPI, HTTPException
# AJOUT 1 : Import CORS
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
# LangChain Imports
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import SystemMessage

# --- Configuration et Modèles ---

# URL du microservice IndexeurSémantique (pour la récupération des chunks)
INDEXER_URL = os.getenv("INDEXER_URL", "http://127.0.0.1:8001") 

# LLM et Chat Model (chargés au démarrage du service)
chat_model: Optional[ChatHuggingFace] = None

def load_llm():
    """Charge le modèle LLM et son wrapper ChatHuggingFace."""
    global chat_model
    
    # Récupérer le token HF depuis l'environnement ou une variable d'initialisation
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        # En production, cela devrait être un échec critique
        print("CRITIQUE: HF_TOKEN non défini. Le service ne pourra pas répondre.")
        return

    try:
        llm = HuggingFaceEndpoint(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",
            huggingfacehub_api_token=hf_token,
            temperature=0.1,
            max_new_tokens=1024,
        )
        chat_model = ChatHuggingFace(llm=llm)
        print("✅ LLM (Mistral-7B) chargé.")
    except Exception as e:
        print(f"⚠️ Erreur de chargement du LLM : {e}")


# --- Schémas de données Pydantic ---

# Schéma pour l'input de la question
class QAInput(BaseModel):
    prompt: str = Field(..., description="La question de l'utilisateur.")
    # Permet d'intégrer l'historique de conversation (facultatif)
    history: List[Dict[str, str]] = Field(default_factory=list, description="Historique de la conversation.")

# Schéma pour la réponse finale
class QAResponse(BaseModel):
    answer: str
    sources: List[str]
    context_chunks: int

# Schéma pour les chunks reçus de l'IndexeurSémantique (doit correspondre au schéma du Microservice 2)
class Chunk(BaseModel):
    content: str
    source: str
    score: float 

class RetrievalResponse(BaseModel):
    chunks: List[Chunk]

# --- Fonctions de Traitement ---

def build_messages(prompt: str, context: str, history: List[Dict[str, str]]):
    """Construit la liste des messages (System, History, User) pour le LLM."""
    messages = [
        SystemMessage(
            content=(
                "Tu es un assistant médical expert. "
                "Réponds uniquement en français et uniquement à partir des documents fournis. "
                "Si l'information n'est pas dans les documents, réponds : "
                "'Je ne trouve pas cette information dans les documents chargés.'"
                "Si la question est hors sujet médical, décline poliment."
                "Si l'utilisateur demande une comparaison entre patients, donne d'abord un tableau comparatif puis explique le."
                
            )
        )
    ]

    # Ajout de l'historique conversationnel (pour le suivi de contexte)
    # L'historique doit être nettoyé pour ne contenir que les clés 'role' et 'content'
    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})

    # Ajouter le prompt enrichi par le contexte RAG
    enriched_prompt = f"Contexte documentaire :\n{context}\n\nQuestion : {prompt}"
    messages.append({"role": "user", "content": enriched_prompt})

    return messages

# --- FastAPI App ---

app = FastAPI(title="LLM QA Microservice")

# --- AJOUT 2 : Configuration CORS pour autoriser Next.js ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Charge le LLM au lancement de l'application."""
    load_llm()

# --- Endpoints ---

@app.post("/ask-qa", response_model=QAResponse)
def ask_qa(input_data: QAInput):
    """
    Orchestre la recherche RAG et génère la réponse finale du LLM.
    """
    if chat_model is None:
        raise HTTPException(status_code=503, detail="Le modèle LLM n'a pas pu être chargé.")

    # 1. Appel HTTP à l'IndexeurSémantique pour la recherche contextuelle
    retrieval_endpoint = f"{INDEXER_URL}/retrieve-chunks"
    
    try:
        # Envoi de la question pour la recherche de similarité
        # On utilise le prompt de l'utilisateur comme corps de la requête
        response = requests.post(
            retrieval_endpoint, 
            json={"question": input_data.prompt, "k": 8, "score_threshold": 0.75}
        )
        response.raise_for_status()
        
        # Validation et récupération des fragments
        retrieval_data = RetrievalResponse.model_validate(response.json())
        relevant_chunks = retrieval_data.chunks

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Erreur de communication avec l'IndexeurSémantique: {e}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de validation des chunks: {e}")

    # 2. Préparation du Contexte et des Sources
    context = "\n\n".join([chunk.content for chunk in relevant_chunks])
    sources = list(set([chunk.source for chunk in relevant_chunks]))
    
    if not context.strip():
        # Si aucun fragment pertinent n'est trouvé
        return QAResponse(
            answer="Je ne trouve pas d'informations pertinentes dans les documents chargés.", 
            sources=[], 
            context_chunks=0
        )

    # 3. Construction du Prompt Final (avec RAG et Historique)
    messages = build_messages(input_data.prompt, context, input_data.history)

    # 4. Appel au LLM
    try:
        answer = chat_model.invoke(messages).content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'appel au LLM: {e}")
    
    # 5. Retour de la Réponse
    return QAResponse(
        answer=answer or "Aucune réponse générée.",
        sources=sources,
        context_chunks=len(relevant_chunks)
    )

# --- Lancement ---
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8002)
import os
import uvicorn
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# LangChain Imports
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import SystemMessage

# --- Configuration et Modèles ---

INDEXER_URL = os.getenv("INDEXER_URL", "http://127.0.0.1:8001") 

chat_model: Optional[ChatHuggingFace] = None

def load_llm():
    global chat_model
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("CRITIQUE: HF_TOKEN non défini.")
        return

    try:
        # Température 0.01 pour rigueur maximale
        llm = HuggingFaceEndpoint(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",
            huggingfacehub_api_token=hf_token,
            temperature=0.01,
            max_new_tokens=1024,
        )
        chat_model = ChatHuggingFace(llm=llm)
        print("✅ LLM (Mistral-7B) chargé.")
    except Exception as e:
        print(f"⚠️ Erreur de chargement du LLM : {e}")


# --- Schémas ---

class QAInput(BaseModel):
    prompt: str = Field(..., description="La question de l'utilisateur.")
    history: List[Dict[str, str]] = Field(default_factory=list)

class QAResponse(BaseModel):
    answer: str
    sources: List[str]
    context_chunks: int

class Chunk(BaseModel):
    content: str
    source: str
    score: float 

class RetrievalResponse(BaseModel):
    chunks: List[Chunk]


def build_rag_messages(prompt: str, context: str, history: List[Dict[str, str]]):
    """
    Prompt 'DRACONIEN' : Interdiction totale de politesse ou de hors-sujet.
    """
    system_instruction = (
        "TASK: You are a strict medical data extraction bot. NOT an assistant.\n"
        "OUTPUT LANGUAGE: FRENCH ONLY.\n\n"
        
        "--- RULES ---\n"
        "1. USE ONLY the provided 'CONTEXTE DOSSIER'.\n"
        "2. IF the answer is found in the context: Answer directly in French. Be concise.\n"
        "3. IF the answer is NOT in the context (e.g., Japan, Recipes, weather, politics...):\n"
        "   YOU MUST OUTPUT EXACTLY THIS PHRASE AND NOTHING ELSE:\n"
        "   'Je suis un assistant médical. Cette demande est hors contexte ou absente du dossier.'\n"
        "4. DO NOT APOLOGIZE. DO NOT SAY 'I'm sorry'. DO NOT PROVIDE THE RECIPE.\n"
        "5. STOP generating immediately after the rejection phrase.\n"
    )
    
    messages = [SystemMessage(content=system_instruction)]

    # On réduit l'historique au strict minimum (1 message) pour éviter qu'il ne s'inspire des bêtises d'avant
    for m in history[-1:]: 
        messages.append({"role": m["role"], "content": m["content"]})

    # Le prompt final
    user_prompt = f"--- CONTEXTE DOSSIER ---\n{context}\n\n--- QUESTION UTILISATEUR ---\n{prompt}"
    messages.append({"role": "user", "content": user_prompt})

    return messages
# --- FastAPI App ---

app = FastAPI(title="LLM QA Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    load_llm()

# --- Endpoints ---

@app.post("/ask-qa", response_model=QAResponse)
def ask_qa(input_data: QAInput):
    if chat_model is None:
        raise HTTPException(status_code=503, detail="Le modèle LLM n'est pas chargé.")

    # 1. RAG : Récupération des documents
    # On a supprimé le filtre Python ici. On fait confiance au Prompt.
    retrieval_endpoint = f"{INDEXER_URL}/retrieve-chunks"
    try:
        response = requests.post(
            retrieval_endpoint, 
            json={"question": input_data.prompt, "k": 6, "score_threshold": 0.75}
        )
        response.raise_for_status()
        relevant_chunks = RetrievalResponse.model_validate(response.json()).chunks
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur Indexeur: {e}")

    # 2. Pas de docs ?
    # Si l'indexeur ne trouve RIEN du tout, on coupe court.
    if not relevant_chunks:
        return QAResponse(
            answer="Je suis un assistant médical. Cette demande est hors contexte ou absente du dossier.", 
            sources=[], 
            context_chunks=0
        )

    # 3. Génération de la réponse
    context = "\n\n".join([f"[Source: {chunk.source}]\n{chunk.content}" for chunk in relevant_chunks])
    sources = list(set([chunk.source for chunk in relevant_chunks]))
    
    messages = build_rag_messages(input_data.prompt, context, input_data.history)
    
    try:
        answer = chat_model.invoke(messages).content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur LLM: {e}")
    
    return QAResponse(
        answer=answer,
        sources=sources,
        context_chunks=len(relevant_chunks)
    )

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8002)
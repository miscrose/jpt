
import os
import uvicorn
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import SystemMessage



INDEXER_URL = os.getenv("INDEXER_URL", "http://127.0.0.1:8001") 

chat_model: Optional[ChatHuggingFace] = None

def load_llm():
    global chat_model
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("CRITIQUE: HF_TOKEN non défini.")
        return

    try:

        llm = HuggingFaceEndpoint(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",
          
            huggingfacehub_api_token=hf_token,
            temperature=0.01,       
            max_new_tokens=2048,    
        )
        chat_model = ChatHuggingFace(llm=llm)
        print("✅ LLM (Mistral-7B) chargé.")
    except Exception as e:
        print(f"⚠️ Erreur de chargement du LLM : {e}")




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
    Prompt 'ARCHITECTE' : Force le Markdown, interdit le bavardage et gère le multi-patient.
    """
    system_instruction = (
        "RÔLE : Tu es un automate d'extraction de données médicales. Tu n'es PAS une personne.\n"
        "LANGUE : FRANÇAIS UNIQUEMENT.\n\n"
        
        "RÈGLES DE FORMATAGE (CRUCIAL) :\n"
        "1. Pour les tableaux, utilise EXCLUSIVEMENT le format Markdown standard avec des barres verticales (|).\n"
        "   Exemple obligatoire :\n"
        "   | Patient | Symptôme |\n"
        "   |---------|----------|\n"
        "   | M. X    | Toux     |\n"
        "2. Assure-toi de faire un saut de ligne après chaque rangée du tableau.\n"
        "3. N'invente JAMAIS de balises comme [Tableau] ou XML.\n\n"
        
        "RÈGLES DE COMPORTEMENT :\n"
        "1. Réponds DIRECTEMENT par le tableau ou l'information.\n"
        "2. NE DIS RIEN D'AUTRE. Pas de bonjour, pas d'intro, pas de 'Voici le tableau'.\n"
        "3. NE SIGNE JAMAIS à la fin (Interdit de dire 'Je suis un assistant...').\n"
        "4. ATTENTION AUX PATIENTS MULTIPLES : Le contexte peut contenir plusieurs dossiers différents.\n"
        "   Ne mélange pas les antécédents d'un patient avec ceux d'un autre. Vérifie bien les séparations.\n\n"
        
        "CAS D'ERREUR :\n"
        "Si l'information n'est PAS dans le 'CONTEXTE DOSSIER', réponds UNIQUEMENT :\n"
        "'Information absente du dossier.'"
    )
    
    messages = [SystemMessage(content=system_instruction)]


    for m in history[-1:]: 
        messages.append({"role": m["role"], "content": m["content"]})


    user_prompt = f"--- CONTEXTE DOSSIER ---\n{context}\n\n--- QUESTION ---\n{prompt}"
    messages.append({"role": "user", "content": user_prompt})

    return messages


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



@app.post("/ask-qa", response_model=QAResponse)
def ask_qa(input_data: QAInput):
    if chat_model is None:
        raise HTTPException(status_code=503, detail="Le modèle LLM n'est pas chargé.")


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


    if not relevant_chunks:
        return QAResponse(
            answer="Je suis un assistant médical. Cette demande est hors contexte ou absente du dossier.", 
            sources=[], 
            context_chunks=0
        )


    context = "\n\n".join([f"[Source: {chunk.source}]\n{chunk.content}" for chunk in relevant_chunks])

    print("==================================================")
    print("🔍 CE QUE L'IA REÇOIT (CONTEXTE) :")
    print(context)
    print("==================================================")
    
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

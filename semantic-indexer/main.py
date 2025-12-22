import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional


from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


VECTOR_FOLDER = os.getenv("VECTOR_FOLDER", "vector_store")
os.makedirs(VECTOR_FOLDER, exist_ok=True)
FAISS_INDEX_PATH = os.path.join(VECTOR_FOLDER, "faiss.index")


embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


vectorstore: Optional[FAISS] = None

def load_vector_store():
    """Charge ou initialise l'index FAISS au démarrage du service."""
    global vectorstore
    

    if os.path.exists(FAISS_INDEX_PATH + ".faiss"):
        try:
            vectorstore = FAISS.load_local(
                VECTOR_FOLDER, 
                embeddings, 
                "faiss.index",
                allow_dangerous_deserialization=True
            )
            print(f"✅ Index FAISS chargé depuis le disque ! ({vectorstore.index.ntotal} documents)")
        except Exception as e:
            print(f"⚠️ Erreur de chargement de l'index : {e}. L'index sera recréé.")
            vectorstore = None
    else:
        print("ℹ️ Aucun index FAISS trouvé. Il sera créé lors de la première ingestion.")
        vectorstore = None



class RetrievalRequest(BaseModel):
    """Schéma pour la requête de recherche de fragments."""
    question: str = Field(..., description="La question de l'utilisateur.")
    k: int = 8
    score_threshold: float = 0.75

class IngestRequest(BaseModel):
    """Schéma pour l'ingestion de contenu."""
    content: str = Field(..., description="Le texte brut du document à indexer.")
    source: str = Field(..., description="Le nom du fichier source (ex: 'doc.pdf').")

class Chunk(BaseModel):
    """Représentation d'un fragment de document pour la réponse de recherche."""
    content: str
    source: str
    score: float 

class RetrievalResponse(BaseModel):
    """Schéma de la réponse pour une recherche sémantique."""
    chunks: List[Chunk] = Field(..., description="Liste des fragments de document pertinents.")



app = FastAPI(title="Semantic Indexer Microservice")

@app.on_event("startup")
async def startup_event():
    """Tente de charger la base vectorielle au lancement de l'application."""
    load_vector_store()

# --- Endpoints ---

@app.post("/index-chunks", status_code=200)
def index_document(request: IngestRequest):
    global vectorstore

    text = request.content
    source = request.source

    if not text.strip():
        raise HTTPException(status_code=400, detail="Contenu du document vide.")

    splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,   
    chunk_overlap=200,  
    separators=["\n\n", "\n", ".", " ", ""] 
)
    chunks = splitter.split_text(text)
    docs = [Document(page_content=c, metadata={"source": source}) for c in chunks]


    if not vectorstore:
        vectorstore = FAISS.from_documents(docs, embeddings)
    else:
        vectorstore.add_documents(docs)


    try:
        vectorstore.save_local(VECTOR_FOLDER, "faiss.index")
        return {"status": "success", "message": f"Indexé : {source} ({len(docs)} morceaux)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde FAISS : {e}")


@app.post("/retrieve-chunks", response_model=RetrievalResponse)
def retrieve_chunks(request: RetrievalRequest):
    if vectorstore is None:

        return RetrievalResponse(chunks=[])
    
    docs_scores = vectorstore.similarity_search_with_score(
        request.question,
        k=request.k
    )
    

    relevant = [
        Chunk(content=doc.page_content, source=doc.metadata["source"], score=score) 
        for doc, score in docs_scores 
        if score < request.score_threshold
    ]


    if not relevant and docs_scores:
        relevant = [
            Chunk(content=doc.page_content, source=doc.metadata["source"], score=score) 
            for doc, score in docs_scores[:3]
        ]
        
    return RetrievalResponse(chunks=relevant)

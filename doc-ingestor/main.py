import os
import uvicorn
import requests
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
# AJOUT 1 : Import du Middleware CORS
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber

# --- Configuration ---

# Chemin de stockage local des documents (pour persistance)
DOCS_FOLDER = os.getenv("DOCS_FOLDER", "documents")
os.makedirs(DOCS_FOLDER, exist_ok=True)

# URL du microservice IndexeurSémantique
INDEXER_URL = os.getenv("INDEXER_URL", "http://127.0.0.1:8001") 

app = FastAPI(title="Document Ingestor Microservice")

# --- AJOUT 2 : Configuration CORS pour autoriser Next.js ---
app.add_middleware(
    CORSMiddleware,
    # On autorise le port 3000 (Next.js) et localhost
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"], # Autorise POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)
# -----------------------------------------------------------

# --- Fonctions de Traitement ---

def pdf_to_text(path: Path) -> str:
    """Extrait le texte de toutes les pages d'un PDF."""
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
        return text
    except Exception as e:
        # En cas de fichier corrompu ou illisible
        raise HTTPException(status_code=500, detail=f"Erreur de lecture PDF: {e}")


# --- Endpoints ---

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Reçoit un fichier PDF, le stocke, le convertit en texte et
    déclenche l'indexation sémantique via une requête HTTP.
    """
    file_path = Path(DOCS_FOLDER) / file.filename

    # 1. Sauvegarde du fichier localement
    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de sauvegarde: {e}")
    finally:
        # Assurez-vous que le fichier est fermé, même en cas d'erreur
        await file.close()

    # 2. Conversion PDF en Texte
    raw_text = pdf_to_text(file_path)
    if not raw_text.strip():
        # Optionnel: Supprimer le fichier s'il est vide
        # os.remove(file_path) 
        raise HTTPException(status_code=400, detail="Le fichier PDF ne contient pas de texte extractible.")

    # 3. Appel HTTP au service IndexeurSémantique
    ingest_endpoint = f"{INDEXER_URL}/index-chunks"
    
    # Payload attendu par IndexeurSémantique
    data = {
        "content": raw_text,
        "source": file.filename
    }

    try:
        # Envoi de la requête à l'IndexeurSémantique
        response = requests.post(ingest_endpoint, json=data)
        response.raise_for_status() # Lève une exception si le statut n'est pas 2xx
        
        # Succès de l'indexation
        return {
            "status": "success",
            "filename": file.filename,
            "indexer_response": response.json()
        }

    except requests.exceptions.RequestException as e:
        # Échec de l'appel au service d'indexation
        raise HTTPException(
            status_code=503, 
            detail=f"Erreur de communication avec l'IndexeurSémantique ({ingest_endpoint}): {e}"
        )
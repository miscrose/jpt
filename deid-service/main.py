import os
import uvicorn
import spacy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

# --- Configuration et Modèles ---

# URL du microservice IndexeurSémantique
INDEXER_URL = os.getenv("INDEXER_URL", "http://127.0.0.1:8001") 

# Modèle NLP (Chargé au démarrage)
nlp = None
MODEL_NAME = "fr_core_news_md" # À adapter selon votre installation

def load_nlp_model():
    """Charge le modèle spaCy pour la reconnaissance d'entités."""
    global nlp
    try:
        # Assurez-vous d'avoir téléchargé ce modèle via python -m spacy download ...
        nlp = spacy.load(MODEL_NAME)
        print(f"✅ Modèle spaCy '{MODEL_NAME}' chargé.")
    except OSError:
        # Gérer le cas où le modèle n'est pas trouvé
        raise EnvironmentError(f"Le modèle spaCy '{MODEL_NAME}' est manquant. Installez-le avec : python -m spacy download {MODEL_NAME}")

# Schémas de données
class DeIDRequest(BaseModel):
    content: str
    source: str

class DeIDResponse(BaseModel):
    anonymized_content: str
    source: str
    
# --- FastAPI App ---
app = FastAPI(title="De-ID Microservice")

@app.on_event("startup")
async def startup_event():
    load_nlp_model()

# --- Endpoint ---

@app.post("/anonymize-text", status_code=200)
def anonymize_and_index(request: DeIDRequest):
    """
    1. Anonymise le texte en utilisant spaCy.
    2. Transmet le texte anonymisé à l'IndexeurSémantique.
    """
    if nlp is None:
        raise HTTPException(status_code=503, detail="Le modèle NLP n'est pas chargé.")

    doc = nlp(request.content)
    anonymized_text = request.content
    
    # 1. Anonymisation (Remplacement des noms/personnes)
    # L'itération se fait à l'envers pour que les index restent valides lors des remplacements
    for ent in reversed(doc.ents):
        # Filtrer sur les entités de type personne (PERSON), lieu (LOC) ou organisation (ORG)
        if ent.label_ in ("PER", "LOC", "ORG"):
            # Exemple simple : remplacer l'entité par une balise générique
            anonymized_text = (
                anonymized_text[:ent.start_char] + 
                f"[{ent.label_}]" + 
                anonymized_text[ent.end_char:]
            )

    # 2. Appel HTTP à l'IndexeurSémantique
    ingest_endpoint = f"{INDEXER_URL}/index-chunks"
    data = {
        "content": anonymized_text,
        "source": request.source
    }

    try:
        response = requests.post(ingest_endpoint, json=data)
        response.raise_for_status() 
        
        return {
            "status": "success",
            "indexer_response": response.json(),
            "anonymized_content_preview": anonymized_text[:200] + "..." # Aperçu pour debug
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Erreur de communication avec l'IndexeurSémantique: {e}"
        )

# --- Lancement ---
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8003)
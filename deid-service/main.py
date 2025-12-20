import os
import uvicorn
import spacy
import re  # Pour les Expressions Régulières
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# --- Configuration ---

INDEXER_URL = os.getenv("INDEXER_URL", "http://127.0.0.1:8001") 

# Modèle NLP
MODEL_NAME = "fr_core_news_md" 
nlp = None
COUNTER_FILE = "patient_counter.txt" 
DEBUG_DIR = "debug_anonymized_docs"

def load_nlp_model():
    """Charge le modèle SpaCy au démarrage."""
    global nlp
    try:
        print(f"⏳ Chargement du modèle spaCy '{MODEL_NAME}'...")
        nlp = spacy.load(MODEL_NAME)
        print(f"✅ Modèle spaCy '{MODEL_NAME}' chargé.")
    except OSError:
        raise EnvironmentError(f"❌ Modèle manquant. Exécutez : python -m spacy download {MODEL_NAME}")

    if not os.path.exists(DEBUG_DIR):
        os.makedirs(DEBUG_DIR)
        print(f"📂 Dossier de debug créé : {DEBUG_DIR}")

# --- FONCTION GESTION COMPTEUR ---
def get_next_patient_id():
    """Gère l'auto-incrémentation des IDs patients."""
    current_id = 1
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                content = f.read().strip()
                if content.isdigit():
                    current_id = int(content)
        except Exception as e:
            print(f"⚠️ Erreur lecture compteur, réinitialisation à 1 : {e}")
            current_id = 1
    
    patient_label = f"Patient_{current_id}"
    
    try:
        with open(COUNTER_FILE, "w") as f:
            f.write(str(current_id + 1))
    except Exception as e:
        print(f"⚠️ Impossible de sauvegarder le compteur : {e}")
        
    return patient_label

# --- Schémas de Données ---

class DeIDRequest(BaseModel):
    content: str
    source: str

class DeIDResponse(BaseModel):
    anonymized_content: str
    source: str

# --- CŒUR DU SYSTÈME : Fonction d'Anonymisation Hybride ---
# MODIFICATION ICI : On ajoute le paramètre 'patient_label'
def advanced_anonymization(text: str, patient_label: str) -> str:
    """
    Remplace les noms par l'ID du patient (ex: Patient_1) pour que le tableau final soit clair.
    """
    
    # 1. Masquer les EMAILS
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_MASQUÉ]', text)
    
    # 2. Masquer les TÉLÉPHONES
    phone_pattern = r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}'
    text = re.sub(phone_pattern, '[TÉL_MASQUÉ]', text)

    # 3. Masquer les Champs de Formulaire (Nom : X, Prénom : Y)
    # ICI C'EST LA MAGIE : On remplace par le label (Patient_1) !
    field_pattern = r'(Nom|Prénom|Patient|Surnom)\s*[:\.]?\s+([A-ZÀ-ÿ][a-zÀ-ÿ]+|[A-Z]{2,})'
    # La regex va écrire : "Nom : Patient_1"
    text = re.sub(field_pattern, f"\\1 : {patient_label}", text, flags=re.IGNORECASE)

    # 4. Masquer les NOMS après civilités (Dr., M., Mme)
    # On fait attention : Si c'est un Dr, on met [MEDECIN] pour ne pas confondre avec le patient
    # Si c'est Monsieur/Madame, on met le patient_label
    text = re.sub(r'(Dr\.?)\s+([A-ZÀ-ÿ][a-zÀ-ÿ]+)', r'\1 [MEDECIN]', text)
    text = re.sub(r'(Monsieur|Madame|M\.|Mme)\s+([A-ZÀ-ÿ][a-zÀ-ÿ]+)', f"\\1 {patient_label}", text)

    # 5. NLP (SpaCy) - Filet de sécurité
    doc = nlp(text)
    entities_to_replace = []
    
    for ent in doc.ents:
        if ent.label_ in ["PER"]: 
            if patient_label not in ent.text and "[MEDECIN]" not in ent.text and "[EMAIL_MASQUÉ]" not in ent.text:
                # On remplace tout nom restant par le label du patient
                entities_to_replace.append((ent.start_char, ent.end_char, patient_label))

    entities_to_replace.sort(key=lambda x: x[0], reverse=True)

    for start, end, label in entities_to_replace:
        current_slice = text[start:end]
        if "[" not in current_slice and "Patient_" not in current_slice: 
            text = text[:start] + label + text[end:]
        
    return text

# --- FastAPI App ---

app = FastAPI(title="De-ID Microservice (Injection ID Patient)")

@app.on_event("startup")
async def startup_event():
    load_nlp_model()

@app.post("/anonymize-text", status_code=200)
def anonymize_and_index(request: DeIDRequest):
    if nlp is None:
        raise HTTPException(status_code=503, detail="Le modèle NLP n'est pas prêt.")

    unique_patient_id = get_next_patient_id()
    print(f"🆔 Nouveau document : {request.source} -> ID attribué : {unique_patient_id}")

    # 1. Exécution de l'anonymisation EN PASSANT L'ID
    try:
        # ON PASSE L'ID ICI !
        clean_text = advanced_anonymization(request.content, unique_patient_id)
        
        # SAUVEGARDE DEBUG
        filename = f"{unique_patient_id}.txt"
        filepath = os.path.join(DEBUG_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"--- SOURCE ORIGINALE : {request.source} ---\n\n")
            f.write(clean_text)
        print(f"💾 Fichier transformé sauvegardé : {filepath}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne d'anonymisation : {e}")

    # 2. Envoi à l'Indexeur (Port 8001)
    ingest_endpoint = f"{INDEXER_URL}/index-chunks"
    
    data = {
        "content": clean_text,
        "source": request.source # On garde le nom du fichier pour l'affichage des sources
    }

    try:
        response = requests.post(ingest_endpoint, json=data)
        response.raise_for_status() 
        
        return {
            "status": "success",
            "message": f"Texte anonymisé avec {unique_patient_id}.",
            "original_filename": request.source,
            "assigned_id": unique_patient_id,
            "anonymized_preview": clean_text[:200]
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur connexion Indexeur (8001): {e}")
        raise HTTPException(status_code=503, detail=f"Indexeur injoignable: {e}")

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8003)
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

# Modèle NLP (Moyen ou Large recommandé pour le français)
MODEL_NAME = "fr_core_news_md" 
nlp = None
COUNTER_FILE = "patient_counter.txt" # Fichier pour stocker le numéro du patient

def load_nlp_model():
    """Charge le modèle SpaCy au démarrage."""
    global nlp
    try:
        print(f"⏳ Chargement du modèle spaCy '{MODEL_NAME}'...")
        nlp = spacy.load(MODEL_NAME)
        print(f"✅ Modèle spaCy '{MODEL_NAME}' chargé.")
    except OSError:
        raise EnvironmentError(f"❌ Modèle manquant. Exécutez : python -m spacy download {MODEL_NAME}")

# --- FONCTION GESTION COMPTEUR (Nouvel Ajout) ---
def get_next_patient_id():
    """
    Gère l'auto-incrémentation des IDs patients.
    Si le fichier n'existe pas, il est créé et initialisé.
    """
    current_id = 1
    
    # 1. Lecture du compteur existant
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                content = f.read().strip()
                if content.isdigit():
                    current_id = int(content)
        except Exception as e:
            print(f"⚠️ Erreur lecture compteur, réinitialisation à 1 : {e}")
            current_id = 1
    
    # 2. Création du Label pour ce document
    patient_label = f"Patient_{current_id}"
    
    # 3. Sauvegarde du PROCHAIN numéro pour le futur
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
def advanced_anonymization(text: str) -> str:
    """
    Combine Regex (Règles strictes) + NLP (IA contextuelle).
    """
    
    # --- ÉTAPE 1 : REGEX (Nettoyage Brutal) ---
    
    # 1. Masquer les EMAILS
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_MASQUÉ]', text)
    
    # 2. Masquer les TÉLÉPHONES
    phone_pattern = r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}'
    text = re.sub(phone_pattern, '[TÉL_MASQUÉ]', text)

    # 3. Masquer les NOMS après civilités (Version Gourmande / Greedy) 🛡️
    civility_pattern = r'(Monsieur|Madame|M\.|Mme|Dr\.?)\s+((?:[A-ZÀ-ÿ][a-zÀ-ÿ]+|[A-Z]{2,})(?:[\s-](?:[A-ZÀ-ÿ][a-zÀ-ÿ]+|[A-Z]{2,}))*)'
    text = re.sub(civility_pattern, r'\1 [NOM_MASQUÉ]', text)

    # --- ÉTAPE 2 : NLP (Pour le reste) ---
    
    doc = nlp(text)
    entities_to_replace = []
    
# --- DANS advanced_anonymization ---
    for ent in doc.ents:
       
        if ent.label_ in ["PER"]: 
            if "[NOM_MASQUÉ]" not in ent.text and "[EMAIL_MASQUÉ]" not in ent.text and "[TÉL_MASQUÉ]" not in ent.text:
                tag = f"[{ent.label_}]" # Deviendra [PER]
                entities_to_replace.append((ent.start_char, ent.end_char, "[NOM_MASQUÉ]")) # On uniformise tout en [NOM_MASQUÉ]
    # --- ÉTAPE 3 : Remplacement ---
    entities_to_replace.sort(key=lambda x: x[0], reverse=True)

    for start, end, label in entities_to_replace:
        current_slice = text[start:end]
        if "[" not in current_slice: 
            text = text[:start] + label + text[end:]
        
    return text

# --- FastAPI App ---

app = FastAPI(title="De-ID Microservice (Hybrid + AutoIncrement)")

@app.on_event("startup")
async def startup_event():
    load_nlp_model()

@app.post("/anonymize-text", status_code=200)
def anonymize_and_index(request: DeIDRequest):
    """
    Reçoit du texte sale -> Nettoie -> Assigne un ID Patient -> Envoie à l'indexeur.
    """
    if nlp is None:
        raise HTTPException(status_code=503, detail="Le modèle NLP n'est pas prêt.")

    # --- NOUVEAU : Génération de l'ID Patient ---
    unique_patient_id = get_next_patient_id()
    print(f"🆔 Nouveau document reçu. Traitement sous l'ID : {unique_patient_id}")

    # 1. Exécution de l'anonymisation
    try:
        clean_text = advanced_anonymization(request.content)
        
        # DEBUG : Affiche dans la console
        print(f"\n🕵️ VÉRIFICATION ANONYMISATION ({unique_patient_id}) :\n{clean_text[:300]}...\n")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne d'anonymisation : {e}")

    # 2. Envoi à l'Indexeur (Port 8001)
    # IMPORTANT : On remplace request.source par unique_patient_id
    ingest_endpoint = f"{INDEXER_URL}/index-chunks"
    data = {
        "content": clean_text,
        "source": unique_patient_id  # <--- C'est ici que ça change !
    }

    try:
        response = requests.post(ingest_endpoint, json=data)
        response.raise_for_status() 
        
        return {
            "status": "success",
            "message": f"Texte anonymisé et indexé sous {unique_patient_id}.",
            "original_filename": request.source,
            "assigned_id": unique_patient_id,
            "anonymized_preview": clean_text[:200]
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur connexion Indexeur (8001): {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Anonymisation OK, mais Indexeur injoignable: {e}"
        )

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8003)
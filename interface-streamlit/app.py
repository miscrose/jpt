import os
import streamlit as st
import requests
from io import BytesIO

# --- Configuration des URL des Microservices ---

# Utilisation des ports définis précédemment
INGESTOR_URL = os.getenv("INGESTOR_URL", "http://127.0.0.1:8000")
LLM_QA_URL = os.getenv("LLM_QA_URL", "http://127.0.0.1:8002")

# --- Fonctions Clients HTTP ---

def client_ingest_pdf(uploaded_file: BytesIO, filename: str) -> requests.Response:
    """
    Appelle le microservice DocIngestor pour uploader et indexer un PDF.
    """
    files = {"file": (filename, uploaded_file, "application/pdf")}
    response = requests.post(f"{INGESTOR_URL}/upload-pdf", files=files)
    return response

def client_ask_qa(prompt: str, history: list) -> requests.Response:
    """
    Appelle le microservice LLMQAModule pour obtenir une réponse RAG.
    """
    # L'historique doit être simplifié pour le transfert HTTP
    simple_history = [{"role": m["role"], "content": m["content"]} for m in history if m["role"] != "system"]
    
    payload = {
        "prompt": prompt,
        "history": simple_history
    }
    response = requests.post(f"{LLM_QA_URL}/ask-qa", json=payload)
    return response

# --- UI (User Interface) ---

st.set_page_config(page_title="DocQA-MS", page_icon="doctor", layout="centered")
st.title("DocQA-MS — Assistant Médical Intelligent")

# 1. Sidebar pour l'Ingestion
with st.sidebar:
    st.header("Documents")
    up = st.file_uploader("Ajouter PDFs", type="pdf", accept_multiple_files=True)
    
    if up:
        for f in up:
            # Nous ne sauvegardons plus localement ici, nous envoyons directement au service
            with st.spinner(f"Indexation de {f.name}..."):
                try:
                    # L'objet file_uploader de Streamlit est lu en mémoire (BytesIO)
                    response = client_ingest_pdf(f, f.name)
                    
                    if response.status_code == 200:
                        st.success(f"Indexé: {f.name}")
                    else:
                        st.error(f"Échec de l'indexation de {f.name}: {response.json().get('detail', 'Erreur inconnue')}")
                except requests.exceptions.ConnectionError:
                    st.error("Erreur: Le service DocIngestor (port 8000) n'est pas accessible.")
                except Exception as e:
                    st.error(f"Erreur inattendue: {e}")

    st.button("Nouvelle conversation", type="primary", on_click=lambda: st.session_state.update(messages=[]))
    
    

# 2. Logique de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.caption(f"Sources : {', '.join(msg['sources'])}")


# Question utilisateur
if prompt := st.chat_input("Votre question ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Réflexion ..."):
            
            # 1. Appel HTTP au LLM QA Module
            try:
                # On passe l'historique complet, le LLMQAModule fera le nettoyage nécessaire
                response = client_ask_qa(prompt, st.session_state.messages)
                response.raise_for_status()
                
                qa_data = response.json()
                reponse = qa_data.get("answer", "Erreur de réponse du LLM.")
                sources = qa_data.get("sources", [])
                
            except requests.exceptions.ConnectionError:
                reponse = "Erreur: Le service LLMQAModule (port 8002) n'est pas accessible."
                sources = []
            except requests.exceptions.HTTPError as e:
                detail = response.json().get('detail', 'Erreur côté serveur.')
                reponse = f"Erreur de traitement (HTTP {response.status_code}): {detail}"
                sources = []
            except Exception as e:
                reponse = f"Erreur inattendue lors de la communication: {e}"
                sources = []

            # 2. Affichage et mise à jour de l'état
            st.markdown(reponse)
            if sources:
                st.caption(f"Sources : {', '.join(sources)}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": reponse,
        "sources": sources if sources else None
    })
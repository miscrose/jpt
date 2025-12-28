# 🏥 MediRAG - Assistant Médical Intelligent & Sécurisé

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Microservices-009688)
![AI](https://img.shields.io/badge/Mistral--7B-RAG-orange)
![Security](https://img.shields.io/badge/DeID-Anonymization-red)

**MediRAG** est une solution d'intelligence artificielle permettant d'interroger des dossiers médicaux (PDF) en langage naturel. Le projet se distingue par une **architecture microservices** et un module d'**anonymisation (De-Identification)** qui protège les données patients avant l'indexation.

## 🏗️ Architecture du Projet

Le système est composé de 5 microservices interconnectés :

```mermaid
graph LR
  PDF(Document PDF) -->|Upload| Ingest[1. Doc-Ingestor :8000]
  Ingest -->|Texte Brut| DeID[2. DeID-Service :8003]
  DeID -->|Texte Anonymisé| Index[3. Semantic-Indexer :8001]
  Index -->|Stockage| DB[(FAISS Vector DB)]
  User(Médecin) -->|Question| LLM[4. LLM-QA :8002]
  LLM -->|Recherche| Index
  Index -->|Contexte| LLM
  LLM -->|Réponse| User

   Les ServicesServicePortDescriptionDoc-Ingestor8000Reçoit les PDF, extrait le texte et l'envoie à l'anonymiseur.DeID-Service8003Sécurité critique. Remplace noms/tél/emails par des ID (ex: Patient_1).Semantic-Indexer8001Transforme le texte en vecteurs (Embeddings) et stocke dans FAISS.LLM-QA8002Le "cerveau". Utilise Mistral-7B pour répondre aux questions via RAG.Frontend3000Interface web (Next.js) pour les utilisateurs.🚀 Installation et Démarrage1. Pré-requisPython 3.9 ou plusNode.js (pour l'interface)Un compte HuggingFace (pour le Token API)2. ConfigurationCréez un fichier .env dans le dossier llm-qa-module :BashHF_TOKEN=votre_token_huggingface_ici
3. Lancer les Microservices (Backend)Ouvrez 4 terminaux séparés et lancez les commandes suivantes :Terminal 1 : IndexeurBashcd semantic-indexer
pip install -r requirements.txt
uvicorn app:app --port 8001 --reload
Terminal 2 : LLM (Questions/Réponses)Bashcd llm-qa-module
pip install -r requirements.txt
uvicorn app:app --port 8002 --reload
Terminal 3 : Anonymiseur (DeID)Bashcd deid-service
pip install -r requirements.txt
python -m spacy download fr_core_news_md
uvicorn app:app --port 8003 --reload
Terminal 4 : Ingestor (Upload)Bashcd doc-ingestor
pip install -r requirements.txt
uvicorn app:app --port 8000 --reload
4. Lancer l'Interface (Frontend)Terminal 5Bashcd interface-nextjs
npm install
npm run dev
Ouvrez votre navigateur sur http://localhost:3000.🔒 Détails TechniquesSécurité (De-Identification)Le service DeID intercepte les documents avant qu'ils ne touchent l'IA.Utilise SpaCy pour détecter les noms (NER).Utilise des Regex pour nettoyer téléphones et emails.Attribue un ID unique (Patient_X) pour garantir la traçabilité sans révéler l'identité.Modèles IALLM : mistralai/Mistral-7B-Instruct-v0.2 (via HuggingFace).Embeddings : sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2.Vector Store : FAISS (Local).

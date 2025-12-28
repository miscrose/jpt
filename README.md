# 🏥 MediRAG - Assistant Médical Intelligent & Sécurisé

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Microservices-009688)
![AI](https://img.shields.io/badge/Mistral--7B-RAG-orange)
![Security](https://img.shields.io/badge/DeID-Anonymization-red)

**MediRAG** est une solution d'intelligence artificielle permettant d'interroger des dossiers médicaux (PDF) en langage naturel.  
Le projet se distingue par une **architecture microservices** et un module d'**anonymisation (De-Identification)** qui protège les données patients avant l'indexation.

## 🏗️ Architecture du Projet

Le système est composé de 5 microservices interconnectés :

```mermaid
graph LR
  PDF[Document PDF] -->|Upload| Ingest[Doc-Ingestor :8000]
  Ingest -->|Texte Brut| DeID[DeID-Service :8003]
  DeID -->|Texte Anonymisé| Index[Semantic-Indexer :8001]
  Index -->|Stockage| DB[(FAISS Vector DB)]
  User[Médecin] -->|Question| LLM[LLM-QA :8002]
  LLM -->|Recherche| Index
  Index -->|Contexte| LLM
  LLM -->|Réponse| User
Détail des Microservices
Service	Port	Description
Doc-Ingestor	8000	Reçoit les PDF, extrait le texte brut et l'envoie au service de sécurité.
DeID-Service	8003	Sécurité. Identifie et masque les données sensibles (Noms, Tels) avant traitement IA.
Semantic-Indexer	8001	Convertit le texte anonymisé en vecteurs (Embeddings) et les stocke.
LLM-QA	8002	Le "Cerveau". Interroge la base vectorielle et génère la réponse via Mistral-7B.
Frontend	3000	Interface utilisateur (Next.js) pour l'upload et le Chat médical.
🚀 Installation et Démarrage (Windows)

Ce projet inclut des scripts d'automatisation pour Windows afin de simplifier l'installation et le lancement.

1. Pré-requis

Python 3.9+ (Assurez-vous qu'il est dans le PATH).

Node.js (Version LTS recommandée).

Un compte HuggingFace (pour obtenir un Token d'accès aux modèles).

2. Installation Automatisée

Lancez simplement le script d'installation des dépendances.

Double-cliquez sur le fichier dependence.bat.

Ce script va mettre à jour pip, installer toutes les librairies Python (FastAPI, LangChain, Spacy...), télécharger le modèle de langue français, et installer les modules Node.js pour le frontend.

3. Configuration API

Avant de lancer, vous devez configurer l'accès au modèle d'IA.

Allez dans le dossier llm-qa-module.

Créez un fichier nommé .env.

Ajoutez votre token HuggingFace à l'intérieur :

HF_TOKEN=votre_token_huggingface_ici

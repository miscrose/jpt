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
  PDF[Document PDF] -->|Upload| Ingest[Doc-Ingestor :8000]
  Ingest -->|Texte Brut| DeID[DeID-Service :8003]
  DeID -->|Texte Anonymisé| Index[Semantic-Indexer :8001]
  Index -->|Stockage| DB[(FAISS Vector DB)]
  User[Médecin] -->|Question| LLM[LLM-QA :8002]
  LLM -->|Recherche| Index
  Index -->|Contexte| LLM
  LLM -->|Réponse| User

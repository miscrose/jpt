@echo off
color 0A
echo ========================================================
echo      LANCEMENT DE L'ARCHITECTURE MICROSERVICES PFE
echo ========================================================
echo.

:: 1. Service d'Ingestion (Port 8000)
echo [1/5] Lancement Ingestor...
start "1. Ingestor (Port 8000)" cmd /k "cd doc-ingestor && python -m uvicorn main:app --reload --port 8000"

:: 2. Service Indexeur Sémantique (Port 8001)
echo [2/5] Lancement Indexeur...
start "2. Indexeur (Port 8001)" cmd /k "cd semantic-indexer && python -m uvicorn main:app --reload --port 8001"

:: 3. Service LLM & QA (Port 8002)
echo [3/5] Lancement LLM Chatbot...
start "3. LLM QA (Port 8002)" cmd /k "cd llm-qa-module && python -m uvicorn main:app --reload --port 8002"

:: 4. Service De-ID / Anonymisation (Port 8003)
echo [4/5] Lancement De-ID...
start "4. De-ID (Port 8003)" cmd /k "cd deid-service && python -m uvicorn main:app --reload --port 8003"

:: 5. Interface Utilisateur (Next.js - Port 3000)
echo [5/5] Lancement Interface Frontend (Next.js)...
timeout /t 2 >nul
:: MODIFICATION ICI : On lance npm run dev pour le site Next.js
start "5. Frontend NextJS (Port 3000)" cmd /k "cd interface-nextjs && npm run dev"

echo.
echo ========================================================
echo      TOUT EST LANCE ! 
echo      Accedez a votre site sur : http://localhost:3000
echo ========================================================
echo.
pause
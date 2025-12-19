@echo off
color 0B
echo ========================================================
echo      INSTALLATION DES DEPENDANCES DU PROJET PFE
echo ========================================================
echo.

echo [1/3] Mise a jour de pip...
python -m pip install --upgrade pip

echo.
echo [2/3] Installation des librairies Python (Nettoyees)...
:: J'ai ajoute chromadb si tu utilises le code que je t'ai donne pour le multi-tenant
pip install fastapi uvicorn pydantic requests python-multipart pdfplumber langchain langchain-huggingface langchain-community python-dotenv faiss-cpu chromadb sentence-transformers spacy huggingface-hub

echo.
echo [3/4] Telechargement du modele de langue Spacy (Francais)...
python -m spacy download fr_core_news_md

echo.
echo [4/4] Installation des dependances Node.js pour l'interface Next.js...
:: Verification de Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Node.js n'est pas installe !
    echo Veuillez installer Node.js depuis https://nodejs.org/
    echo.
    pause
    exit /b 1
)

:: Affichage de la version de Node.js
echo Version de Node.js installee :
node --version
echo.

:: Installation des dependances Next.js
cd interface-nextjs
if not exist "package.json" (
    echo ERREUR: Le dossier interface-nextjs n'existe pas ou package.json introuvable !
    cd ..
    pause
    exit /b 1
)

echo Installation des packages de base (npm install)...
call npm install

echo.
echo [AJOUT] Installation du plugin pour les tableaux (remark-gfm)...
call npm install remark-gfm

cd ..

echo.
echo ========================================================
echo      INSTALLATION TERMINEE AVEC SUCCES !
echo ========================================================
echo Tu peux maintenant lancer 'runall.bat' pour les services Python
echo et 'npm run dev' dans interface-nextjs pour le frontend
echo.
pause
import os
import uvicorn
import requests
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber



DOCS_FOLDER = os.getenv("DOCS_FOLDER", "documents")
os.makedirs(DOCS_FOLDER, exist_ok=True)


ANONYMIZER_SERVICE_URL = os.getenv("ANONYMIZER_URL", "http://127.0.0.1:8003") 

app = FastAPI(title="Document Ingestor Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def pdf_to_text(path: Path) -> str:
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de lecture PDF: {e}")



@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    1. Reçoit le PDF.
    2. Extrait le texte brut (sale).
    3. L'envoie à l'ANONYMISEUR (qui l'enverra ensuite à l'indexeur).
    """
    file_path = Path(DOCS_FOLDER) / file.filename

  
    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de sauvegarde: {e}")
    finally:
        await file.close()


    raw_text = pdf_to_text(file_path)
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Le fichier PDF est vide ou illisible.")


    target_endpoint = f"{ANONYMIZER_SERVICE_URL}/anonymize-text"
    
    data = {
        "content": raw_text,
        "source": file.filename
    }

    try:
  
        response = requests.post(target_endpoint, json=data)
        response.raise_for_status()
        
        return {
            "status": "success",
            "filename": file.filename,
            "pipeline_info": "Envoyé à l'anonymiseur (8003)",
            "anonymizer_response": response.json()
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Erreur de communication avec l'Anonymiseur (Port 8003): {e}"
        )

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)

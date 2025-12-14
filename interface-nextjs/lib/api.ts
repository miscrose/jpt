// Configuration des URLs des microservices
const INGESTOR_URL = process.env.NEXT_PUBLIC_INGESTOR_URL || 'http://127.0.0.1:8000';
const LLM_QA_URL = process.env.NEXT_PUBLIC_LLM_QA_URL || 'http://127.0.0.1:8002';

export interface QARequest {
  prompt: string;
  history: Array<{ role: string; content: string }>;
}

export interface QAResponse {
  answer: string;
  sources: string[];
  context_chunks: number;
}

export interface UploadResponse {
  status: string;
  filename: string;
  indexer_response?: {
    status: string;
    message: string;
  };
}

// Uploader un PDF
export async function uploadPDF(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${INGESTOR_URL}/upload-pdf`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || `Erreur HTTP ${response.status}`);
  }

  return response.json();
}

// Poser une question
export async function askQuestion(
  prompt: string,
  history: Array<{ role: string; content: string }>
): Promise<QAResponse> {
  const payload: QARequest = {
    prompt,
    history: history.map((msg) => ({
      role: msg.role,
      content: msg.content,
    })),
  };

  const response = await fetch(`${LLM_QA_URL}/ask-qa`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || `Erreur HTTP ${response.status}`);
  }

  return response.json();
}


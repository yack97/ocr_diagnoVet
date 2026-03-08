import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe (entorno local)
load_dotenv()

# --- Google Cloud Config ---
PROJECT_ID = os.getenv("PROJECT_ID", "immersion-005")
LOCATION = os.getenv("LOCATION", "europe-west1") # Usado para Document AI y Vertex AI

# --- Storage Config ---
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "veterinaria-diagno-vet")
FOLDER_PENDING = "faltantes_por_procesar"
FOLDER_PROCESSED = "procesados"
FOLDER_ERRORS = "errores"
FOLDER_LOGS = "logs"

# --- Firestore Config ---
FIRESTORE_DATABASE = os.getenv("FIRESTORE_DATABASE", "diagnovet")
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "extracciones_veterinaria")

# --- Document AI Config ---
DOCAI_PROCESSOR_ID = os.getenv("DOCAI_PROCESSOR_ID", "tu-processor-id")

# --- Vertex AI Config ---
VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-1.5-pro-preview-0409") # Puedes ajustarlo al modelo que prefieras

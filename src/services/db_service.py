from google.cloud import firestore
from src.config.settings import PROJECT_ID, FIRESTORE_DATABASE, FIRESTORE_COLLECTION
from src.models.schemas import ProcessingResult

def get_firestore_client() -> firestore.Client:
    return firestore.Client(project=PROJECT_ID, database=FIRESTORE_DATABASE)

def save_extraction_data(data: ProcessingResult) -> str:
    """
    Guarda el objeto ProcessingResult validado (Pydantic a dict) en Firestore.
    """
    db = get_firestore_client()
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(data.doc_id)
    doc_ref.set(data.model_dump())
    return data.doc_id

def get_extraction_data(doc_id: str) -> dict | None:
    """
    Recupera un documento procesado por su ID.
    """
    db = get_firestore_client()
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None

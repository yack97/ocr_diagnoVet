from google.cloud import documentai
from google.api_core.client_options import ClientOptions
from src.config.settings import PROJECT_ID, LOCATION, DOCAI_PROCESSOR_ID

def extract_text_with_docai(pdf_bytes: bytes) -> str:
    """
    Usa Google Cloud Document AI para extraer el texto crudo del PDF.
    
    Requiere un procesador OCR genérico creado en la consola de Document AI.
    """
    if not PROJECT_ID or not DOCAI_PROCESSOR_ID:
        raise ValueError("Falta configurar PROJECT_ID o DOCAI_PROCESSOR_ID")
        
    client_options = ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=client_options)
    
    # El nombre de recurso completo del procesador
    name = client.processor_path(PROJECT_ID, LOCATION, DOCAI_PROCESSOR_ID)
    
    # Cargar el PDF en memoria para procesarlo
    raw_document = documentai.RawDocument(content=pdf_bytes, mime_type="application/pdf")
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    
    try:
        result = client.process_document(request=request)
        document = result.document
        return document.text
    except Exception as e:
        print(f"Error en Document AI OCR: {e}")
        raise e

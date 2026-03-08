import fitz # PyMuPDF
from google.cloud import documentai
from google.api_core.client_options import ClientOptions
from src.config.settings import PROJECT_ID, DOCAI_LOCATION, DOCAI_PROCESSOR_ID

if not PROJECT_ID or not DOCAI_PROCESSOR_ID:
    raise ValueError("Falta configurar PROJECT_ID o DOCAI_PROCESSOR_ID")

# Global Document AI Client for Connection Pooling
_docai_client_options = ClientOptions(api_endpoint=f"{DOCAI_LOCATION}-documentai.googleapis.com")
_docai_client = documentai.DocumentProcessorServiceClient(client_options=_docai_client_options)
_docai_processor_name = _docai_client.processor_path(PROJECT_ID, DOCAI_LOCATION, DOCAI_PROCESSOR_ID)

def extract_text_with_docai(pdf_bytes: bytes) -> str:
    """
    Usa Google Cloud Document AI para extraer el texto crudo del PDF.
    Soporta documentos > 30 páginas dividiéndolos en fragmentos.
    """
    
    # Abrir PDF con PyMuPDF para contar y dividir
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    CHUNK_SIZE = 15 
    extracted_full_text = ""
    
    # Procesar en fragmentos de 15 páginas
    for start_page in range(0, total_pages, CHUNK_SIZE):
        end_page = min(start_page + CHUNK_SIZE - 1, total_pages - 1)
        
        # Crear un nuevo PDF temporal solo con este fragmento
        chunk_doc = fitz.open()
        chunk_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)
        chunk_bytes = chunk_doc.tobytes()
        chunk_doc.close()
        
        raw_document = documentai.RawDocument(content=chunk_bytes, mime_type="application/pdf")
        request = documentai.ProcessRequest(name=_docai_processor_name, raw_document=raw_document)
        
        try:
            result = _docai_client.process_document(request=request)
            extracted_full_text += result.document.text + "\n\n"
        except Exception as e:
            print(f"Error en Document AI OCR (Páginas {start_page}-{end_page}): {e}")
            doc.close()
            raise e
            
    doc.close()
    return extracted_full_text.strip()

import functions_framework
from flask import jsonify

from src.services.ocr_service import extract_data_from_pdf
from src.services.vertex_service import analyze_with_vertex_ai
from src.services.storage_service import upload_images_to_gcs
from src.services.db_service import save_extraction_data, get_extraction_data
from src.utils.pdf_utils import extract_images_from_pdf
from src.utils.logger import get_logger

logger = get_logger(__name__)

@functions_framework.http
def process_veterinary_doc(request):
    """
    HTTP Cloud Function.
    Puedes usar este único entrypoint y enrutar basado en el método o path, 
    o crear funciones desplegadas por separado.
    """
    try:
        if request.method == 'GET':
            # Endpoint para recuperar el JSON con metadatos e imágenes
            doc_id = request.args.get('doc_id')
            if not doc_id:
                return jsonify({"error": "Falta parámetro doc_id"}), 400
            
            data = get_extraction_data(doc_id)
            if not data:
                return jsonify({"error": "No encontrado"}), 404
            
            return jsonify(data), 200

        if request.method == 'POST':
            # 1. Obtener el archivo PDF del request
            # request.files.get('file') ...
            
            # 2. Extraer información estructurada usando Document AI
            # extracted_text = extract_data_from_pdf(pdf_content)
            
            # 3. Extraer imágenes RX usando utilitario de PDF (Ej. PyMuPDF)
            # image_bytes_list = extract_images_from_pdf(pdf_content)
            
            # 4. (Opcional) Analizar texto o imágenes con Vertex AI si Document AI no es suficiente
            # vertex_analysis = analyze_with_vertex_ai(extracted_text, image_bytes_list)

            # 5. Subir imágenes extraídas a GCS
            # image_urls = upload_images_to_gcs(image_bytes_list)
            
            # 6. Guardar metadatos en Firestore / Cloud SQL
            # doc_id = save_extraction_data(metadata_dict, image_urls)
            
            return jsonify({
                "message": "Procesamiento exitoso",
                "doc_id": "generado_por_db"
            }), 201

        return jsonify({"error": "Método no soportado"}), 405

    except Exception as e:
        logger.error(f"Error procesando la solicitud: {e}")
        return jsonify({"error": str(e)}), 500

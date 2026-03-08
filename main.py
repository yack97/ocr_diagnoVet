import os
from flask import Flask, request, jsonify
import uuid
from datetime import datetime

from src.config.settings import GCS_BUCKET_NAME
from src.services.ocr_service import extract_text_with_docai
from src.services.vertex_service import analyze_with_vertex_ai
from src.services.storage_service import save_document_state
from src.services.db_service import save_extraction_data, get_extraction_data
from src.models.schemas import ProcessingResult, VetExtractionResult
from src.utils.pdf_utils import extract_images_from_pdf_bytes
from src.utils.logger import get_logger

import firebase_admin
from firebase_admin import auth, credentials

# Inicializar Firebase Admin usando las credenciales por defecto del entorno de GCP
if not firebase_admin._apps:
    firebase_admin.initialize_app()

logger = get_logger(__name__)

# Aplicación Flask para Cloud Run standard WSGI
app = Flask(__name__)

@app.route("/", methods=["GET", "POST", "OPTIONS"])
def process_veterinary_doc():
    """
    HTTP Cloud Run Endpoint para procesar PDFs veterinarios de forma síncrona.
    """
    # Configurar CORS (Cross-Origin Resource Sharing)
    headers = {
        'Access-Control-Allow-Origin': '*', # En prod: 'https://tu-app.web.app'
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }

    # Preflight request. Responde a OPTIONS rápidamente.
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    # --- Verificación de Autenticación de Firebase ---
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning("Intento de acceso denegado: Token ausente o formato inválido.")
        return (jsonify({"error": "No autorizado. Token requerido."}), 401, headers)
    
    id_token = auth_header.split('Bearer ')[1]
    
    try:
        # Verifica el token contra los servidores de Google/Firebase
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        logger.info(f"Usuario autenticado exitosamente: {uid}")
    except Exception as e:
        logger.warning(f"Intento de acceso con token inválido o expirado: {e}")
        return (jsonify({"error": "No autorizado. Token inválido."}), 401, headers)

    try:
        # --- GET Endpoint ---
        if request.method == 'GET':
            doc_id = request.args.get('doc_id')
            if not doc_id:
                return (jsonify({"error": "Falta parámetro doc_id"}), 400, headers)
            
            data = get_extraction_data(doc_id)
            if not data:
                return (jsonify({"error": f"Documento con ID {doc_id} no encontrado"}), 404, headers)
            
            return (jsonify(data), 200, headers)

        # --- POST Endpoint (Procesamiento de múltiples PDFs) ---
        if request.method == 'POST':
            if 'files' not in request.files:
                return (jsonify({"error": "No se encontraron archivos en la clave 'files'"}), 400, headers)
            
            files = request.files.getlist('files')
            if not files:
                return (jsonify({"error": "La lista de archivos está vacía"}), 400, headers)

            batch_id = str(uuid.uuid4())
            results = []

            for file in files:
                doc_id = str(uuid.uuid4())
                filename = file.filename
                
                logger.info(f"Procesando archivo: {filename} (Doc ID: {doc_id})")
                
                try:
                    # 1. Leer el archivo PDF en memoria
                    pdf_bytes = file.read()
                    
                    if not pdf_bytes:
                         raise ValueError("El archivo está vacío.")

                    # 2. Extraer imágenes (Rayos X) del PDF
                    logger.info("Extrayendo imágenes...")
                    images_list = extract_images_from_pdf_bytes(pdf_bytes)
                    
                    # 3. Extraer texto con Document AI
                    logger.info("Extrayendo texto con Document AI...")
                    extracted_text = extract_text_with_docai(pdf_bytes)
                    
                    # 4. Analizar el texto con Vertex AI para estructurarlo
                    logger.info("Analizando texto con Vertex AI...")
                    vertex_json = analyze_with_vertex_ai(extracted_text)
                    
                    # 5. Guardar archivos (PDF, Text, JSON, Imgs) en GCS (Manejo de carpetas)
                    logger.info("Guardando estado en Storage...")
                    gcs_urls = save_document_state(
                        batch_id=batch_id,
                        doc_id=doc_id,
                        pdf_bytes=pdf_bytes,
                        extracted_text=extracted_text,
                        images_list=images_list,
                        json_data_str=str(vertex_json),
                        estado="EXITO"
                    )
                    
                    # 6. Guardar en Firestore
                    logger.info("Guardando en Firestore...")
                    vet_result = VetExtractionResult(**vertex_json)
                    
                    processing_result = ProcessingResult(
                        doc_id=doc_id,
                        batch_id=batch_id,
                        fecha_procesamiento=datetime.utcnow().isoformat() + "Z",
                        estado="PROCESADO",
                        metadatos_extraidos=vet_result,
                        imagenes_urls=gcs_urls.get("imagenes", []),
                        txt_url=gcs_urls.get("txt", "")
                    )
                    
                    save_extraction_data(processing_result)
                    
                    results.append({
                        "filename": filename,
                        "doc_id": doc_id,
                        "status": "success",
                        "datos_extraidos": vertex_json,
                        "imagenes_urls": gcs_urls.get("imagenes", [])
                    })

                    
                except Exception as e:
                    logger.error(f"Error procesando {filename}: {e}")
                    
                    # Guardar log de error en Storage
                    try:
                        save_document_state(
                            batch_id=batch_id,
                            doc_id=doc_id,
                            pdf_bytes=pdf_bytes if 'pdf_bytes' in locals() else b"",
                            extracted_text="",
                            images_list=[],
                            json_data_str="",
                            estado="ERROR",
                            error_msg=str(e)
                        )
                    except Exception as nested_e:
                        logger.error(f"Falla crítica guardando error en Storage: {nested_e}")

                    results.append({
                        "filename": filename,
                        "doc_id": doc_id,
                        "status": "error",
                        "error_message": str(e)
                    })

            # Retornar el resumen de todo el lote procesado
            return (jsonify({
                "message": f"Lote {batch_id} procesado",
                "batch_id": batch_id,
                "resultados": results
            }), 201, headers)

        return (jsonify({"error": "Método no soportado"}), 405, headers)

    except Exception as e:
        logger.error(f"Error crítico en la Cloud Function: {e}")
        return (jsonify({"error": "Error interno del servidor", "details": str(e)}), 500, headers)

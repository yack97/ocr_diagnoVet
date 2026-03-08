import os
from google.cloud import storage
from src.config.settings import GCS_BUCKET_NAME, FOLDER_PENDING, FOLDER_PROCESSED, FOLDER_ERRORS, FOLDER_LOGS

def get_storage_client() -> storage.Client:
    return storage.Client()

def get_bucket():
    client = get_storage_client()
    return client.bucket(GCS_BUCKET_NAME)

def upload_to_gcs(file_data: bytes, destination_blob_name: str, content_type: str = "application/pdf") -> str:

    bucket = get_bucket()
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(file_data, content_type=content_type)
    return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"

def move_blob(source_blob_name: str, destination_blob_name: str):

    bucket = get_bucket()
    source_blob = bucket.blob(source_blob_name)
    
    # Copiar al nuevo destino
    new_blob = bucket.copy_blob(source_blob, bucket, destination_blob_name)
    
    # Eliminar el original
    source_blob.delete()
    return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"

def save_document_state(
    batch_id: str, 
    doc_id: str, 
    pdf_bytes: bytes, 
    extracted_text: str, 
    images_list: list[tuple[str, bytes]],
    json_data_str: str,
    estado: str = "EXITO",
    error_msg: str = ""
) -> dict:

    # 1. Definir carpeta base
    base_folder = FOLDER_PROCESSED if estado == "EXITO" else FOLDER_ERRORS
    doc_folder = f"{base_folder}/{batch_id}/{doc_id}"
    
    urls = {}
    
    # 2. Subir PDF original
    pdf_path = f"{doc_folder}/documento_original.pdf"
    urls["pdf"] = upload_to_gcs(pdf_bytes, pdf_path, "application/pdf")
    
    # Si hubo error, guardamos el log y terminamos temprano
    if estado != "EXITO":
        error_path = f"{FOLDER_LOGS}/{batch_id}/{doc_id}_error.log"
        urls["log"] = upload_to_gcs(error_msg.encode('utf-8'), error_path, "text/plain")
        return urls

    # 3. Guardar el info.txt (texto crudo de OCR)
    txt_path = f"{doc_folder}/info.txt"
    urls["txt"] = upload_to_gcs(extracted_text.encode('utf-8'), txt_path, "text/plain")
    
    # 4. Guardar data.json (El resultado de Vertex AI estructurado)
    json_path = f"{doc_folder}/data.json"
    urls["json_backup"] = upload_to_gcs(json_data_str.encode('utf-8'), json_path, "application/json")
    
    # 5. Guardar imágenes
    img_urls = []
    for img_filename, img_bytes in images_list:
        img_path = f"{doc_folder}/imagenes/{img_filename}"
        img_url = upload_to_gcs(img_bytes, img_path, "image/jpeg")
        img_urls.append(img_url)
        
    urls["imagenes"] = img_urls
    
    # 6. Guardar log de éxito
    log_path = f"{FOLDER_LOGS}/{batch_id}/{doc_id}_success.log"
    upload_to_gcs(f"Procesado con éxito. DOC ID: {doc_id}".encode('utf-8'), log_path, "text/plain")
    
    return urls

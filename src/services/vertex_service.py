import vertexai
from vertexai.generative_models import GenerativeModel, Part
from src.config.settings import PROJECT_ID, VERTEX_LOCATION, VERTEX_MODEL
import json

# Global Vertex AI Initialization for Connection Pooling
vertexai.init(project=PROJECT_ID, location=VERTEX_LOCATION)
_vertex_model = GenerativeModel(VERTEX_MODEL)

def analyze_with_vertex_ai(extracted_text: str) -> dict:
    
    prompt = f"""
    Eres un analista experto en registros veterinarios. 
    Analiza el siguiente texto extraído de un historial médico veterinario y estructúralo 
    ESTRICTAMENTE en un formato JSON como este:
    {{
        "paciente": "Nombre del paciente o identificación",
        "propietario": "Nombre o identificación del propietario",
        "veterinario": "Nombre o identificación del médico veterinario tratante",
        "diagnostico": "Resumen o texto exacto del diagnóstico o hallazgos",
        "recomendaciones": "Recomendaciones, tratamiento a seguir o próximos pasos"
    }}
    
    Reglas:
    1. Responde ÚNICAMENTE con el objeto JSON válido, sin delimitadores de markdown (como ```json) ni texto adicional.
    2. Si no encuentras un dato, coloca null o una cadena vacía "".
    3. Trata de mantener fielidad a lo que dice el documento en 'diagnostico' y 'recomendaciones'.
    
    TEXTO DEL HISTORIAL:
    {extracted_text}
    """
    
    # Generar contenido
    response = _vertex_model.generate_content(prompt)
    
    try:
        # Se limpia posibles retornos de markdown (```json o ```)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        extracted_data = json.loads(clean_text)
        return extracted_data
    except Exception as e:
        print(f"Error parseando JSON de Vertex AI: {e}")
        return {
            "paciente": "",
            "propietario": "",
            "veterinario": "",
            "diagnostico": response.text,
            "recomendaciones": ""
        }

def filter_medical_images(images_list: list[tuple[str, bytes]]) -> list[tuple[str, bytes]]:
    """
    Usa la capacidad multimodal de Gemini 2.0 Flash para mirar todas las imágenes 
    extraídas y filtrar únicamente las que corresponden a estudios médicos 
    (Radiografías, Ecografías, etc.), descartando por completo logotipos o fotos random.
    """
    if not images_list:
        return []
    
    prompt = """
    Te pasaré una lista de imágenes que fueron extraídas de un archivo PDF veterinario.
    Tu objetivo como especialista es identificar visualmente cuáles de estas imágenes son **escaneos médicos reales** (como radiografías, ecografías, resonancias magnéticas, etc).
    Ignora por completo y descarta: logotipos de clínicas, fotos de decoración, iconografía, fondos en blanco o firmas.
    
    Importante: Devuelve ÚNICAMENTE un arreglo JSON válido (sin formato markdown extra) con los NOMBRES EXACTOS (Filename) de las imágenes que sí son escaneos médicos. Si ninguna lo es, devuelve [].
    Ejemplo de salida estricta:
    [
      "pag1_img1.jpeg",
      "pag2_img3.png"
    ]
    """
    
    contents = [prompt]
    for filename, img_bytes in images_list:
        # Simplificamos el MimeType
        mime_type = "image/png" if filename.lower().endswith("png") else "image/jpeg"
        # Agregar contexto a Gemini de cuál es el archivo que está viendo
        contents.append(f"Filename: {filename}")
        contents.append(Part.from_data(data=img_bytes, mime_type=mime_type))
    
    try:
        response = _vertex_model.generate_content(contents)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        valid_filenames = json.loads(clean_text)
        
        # Quedarse solo con los archivos que pasaron el filtro de Gemini
        valid_images = [
            (fname, b) for fname, b in images_list if fname in valid_filenames
        ]
        return valid_images
    except Exception as e:
        print(f"Error en filtro multimodal de imágenes: {e}")
        return images_list # Ante un error en la IA, fallar de manera segura devolviendo todas

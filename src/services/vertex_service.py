import vertexai
from vertexai.generative_models import GenerativeModel, Part
from src.config.settings import PROJECT_ID, LOCATION, VERTEX_MODEL
import json

def analyze_with_vertex_ai(extracted_text: str) -> dict:
    """
    Toma el texto crudo del PDF y usa Gemini vía Vertex AI para extraer 
    la estructura JSON requerida.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    # Recomendado: Gemini 1.5 Pro para este tipo de tareas de extracción complejas
    model = GenerativeModel(VERTEX_MODEL)
    
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
    response = model.generate_content(prompt)
    
    try:
        # Se limpia posibles retornos de markdown (```json o ```)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        extracted_data = json.loads(clean_text)
        return extracted_data
    except Exception as e:
        print(f"Error parseando JSON de Vertex AI: {e}")
        # Retorno de fallback por si Gemini no cumple el formato
        return {
            "paciente": "",
            "propietario": "",
            "veterinario": "",
            "diagnostico": response.text, # Guarda la salida completa cruda si falla
            "recomendaciones": ""
        }

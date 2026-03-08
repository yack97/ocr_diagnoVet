# 🐾 DiagnoVet - API OCR y Procesamiento de Documentos Veterinarios

Microservicio desplegado en **Google Cloud Run** encargado de recibir historias clínicas, informes ecográficos y radiográficos en formato PDF, extraer su texto e imágenes, estructurar el diagnóstico utilizando Inteligencia Artificial (Vertex AI / Gemini) y almacenar los resultados en la nube.

---

## 🏗️ Arquitectura y Flujo de Datos

El sistema está diseñado para manejar múltiples conexiones concurrentes y PDFs multipágina pesados.

1. **Autenticación (Firebase Auth)**: 
   El frontend envía el PDF junto a un Token JWT (`Authorization: Bearer <TOKEN>`). El backend en Flask valida este token usando Firebase Admin SDK antes de procesar cualquier dato.

2. **Extracción de Imágenes (PyMuPDF)**:
   El servicio escanea todas las páginas del PDF extrayendo imágenes incrustadas (radiografías, ecografías).

3. **Filtro de IA Multimodal (Vertex AI - Gemini 2.0 Flash)**:
   Las imágenes extraídas se envían a Gemini 2.0 Flash, el cual actúa como un "especialista". Analiza visualmente las imágenes, **descarta logotipos, firmas o fondos** y conserva únicamente los escaneos médicos reales.

4. **Extracción de Texto (Document AI)**:
   Si el PDF tiene más de 15 páginas, el sistema lo fragmenta en la memoria (para evadir límites de la API síncrona). Google Cloud Document AI extrae todo el texto crudo del documento.

5. **Estructuración Semántica (Vertex AI - Gemini 2.0 Flash)**:
   El texto crudo es enviado a Gemini, el cual, gracias al prompt diseñado, comprende el contexto veterinario y devuelve un objeto `JSON` estructurado y limpio con: Paciente, Propietario, Médico Tratamiente, Diagnóstico y Recomendaciones.

6. **Almacenamiento (Cloud Storage & Firestore)**:
   - **Google Cloud Storage**: Guarda de forma organizada el PDF original, archivo de texto base, y las imágenes validadas separadas por el estado `procesados/` o `errores/`.
   - **Firestore**: Almacena el `JSON` final estructurado (como NoSQL) junto con las URLs públicas de las imágenes de Storage, listo para ser consumido por el frontend.

---

## 🛠️ Stack Tecnológico

*   **Backend Framework:** Python 3.11+ / Flask / Gunicorn
*   **Gestión de APIs Cloud:** Google Cloud Run (Serverless)
*   **Inteligencia Artificial:**
    *   **Document AI**: Extractor OCR preentrenado.
    *   **Vertex AI (Gemini 2.0)**: IA Generativa Multimodal para estructura de datos y clasificación de imágenes.
*   **Base de Datos NoSQL:** Google Cloud Firestore
*   **Almacenamiento No Estructurado:** Google Cloud Storage
*   **Seguridad:** Firebase Admin SDK (JWT Auth)

---

## 📁 Estructura del Proyecto

```text
/
├── .env.example            # Plantilla de variables de entorno
├── .gitignore              
├── Procfile                # Archivo de arranque para Cloud Run (usa Gunicorn)
├── requirements.txt        # Dependencias de Python (`Flask`, `google-cloud-*`, `PyMuPDF`, etc)
├── main.py                 # Endpoint principal de la API (`/`) - Ruta Flask
└── src/
    ├── api/                
    │   └── routes.py       # (Opcional) Modulación de rutas futuras
    ├── config/             
    │   └── settings.py     # Manejo centralizado de variables de entorno globales
    ├── models/             
    │   └── schemas.py      # Declaración de tipos (Pydantic / Dataclasses) para Firestore
    ├── services/           
    │   ├── db_service.py       # Lógica transaccional Firestore
    │   ├── ocr_service.py      # Lógica de Document AI y fragmentación de PDFs gigantes
    │   ├── storage_service.py  # Lógica de subidas GCS y copia de blobs
    │   └── vertex_service.py   # Invocación a Gemini 2.0 (Estructurador JSON + Filtro Imagen)
    └── utils/              
        ├── logger.py           # Sistema centralizado de tracking / debugging de consola
        └── pdf_utils.py        # Funciones que usan PyMuPDF (fitz)
```

---

## ⚙️ Configuración (.env)

El proyecto requiere un archivo `.env` en local o declarar estas variables en el panel de Cloud Run:

```ini
# Google Cloud
PROJECT_ID=immersion-XXXX
LOCATION=europe-west1          # Región en donde levanta el contenedor de Cloud Run
DOCAI_LOCATION=eu              # Ubicación macrorregional del procesador de DocAI
VERTEX_LOCATION=us-central1    # Ubicación del proveedor de Gemini (Para garantizar Gemini 2.0)

# Cloud Storage
GCS_BUCKET_NAME=veterinaria-diagno-vet

# Firestore
FIRESTORE_DATABASE=diagnovet
FIRESTORE_COLLECTION=extracciones_veterinaria

# Id's Especificos
DOCAI_PROCESSOR_ID=tu_codigo_de_procesador
VERTEX_MODEL=gemini-2.0-flash-001
```

---

## 🚀 Despliegue en Cloud Run

La forma en que este código está adaptado le permite ser totalmente desplegado desde el código fuente sin Dockerfile usando Cloud Buildpacks.

```bash
gcloud run deploy ocr-veterinaria \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \  # El código interno maneja Firebase Auth, por lo que el Invoker puede ser allUsers
  --project=immersion-005-7e407 
```

**Nota sobre `Procfile`**:
El archivo `Procfile` (`web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 main:app`) es de vital importancia, pues le instruye al Buildpack de Google cómo encender la aplicación Flask en producción saltándose los viejos wrappers (functions-framework).

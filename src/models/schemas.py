from pydantic import BaseModel, Field
from typing import List, Optional

class VetExtractionResult(BaseModel):
    paciente: Optional[str] = Field(description="Nombre o identificación del paciente (mascota)")
    propietario: Optional[str] = Field(description="Nombre o identificación del propietario de la mascota")
    veterinario: Optional[str] = Field(description="Nombre o identificación del médico veterinario tratante")
    diagnostico: Optional[str] = Field(description="Diagnóstico principal o hallazgos detectados")
    recomendaciones: Optional[str] = Field(description="Recomendaciones, tratamiento a seguir o próximos pasos")

class ProcessingResult(BaseModel):
    doc_id: str
    batch_id: str
    fecha_procesamiento: str
    estado: str
    metadatos_extraidos: VetExtractionResult
    imagenes_urls: List[str]
    txt_url: Optional[str]
    error_msg: Optional[str] = None

import fitz  # PyMuPDF
import io

def extract_images_from_pdf_bytes(pdf_bytes: bytes) -> list[tuple[str, bytes]]:
    """
    Extrae todas las imágenes incrustadas dentro de un PDF en formato de bytes.
    Retorna una lista de tuplas: (nombre_archivo_sugerido, bytes_de_imagen).
    """
    images = []
    try:
        # Abrir el documento desde memoria
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        image_counter = 1
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list, start=1):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Nombre sugerido: pagX_imgY.ext
                filename = f"pag{page_num+1}_img{img_index}.{image_ext}"
                images.append((filename, image_bytes))
                image_counter += 1
                
        doc.close()
    except Exception as e:
        print(f"Error extrayendo imágenes del PDF: {e}")
        
    return images

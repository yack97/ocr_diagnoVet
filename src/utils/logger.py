import logging
import sys

def get_logger(name: str) -> logging.Logger:

    logger = logging.getLogger(name)
    
    # Previene que se añadan múltiples handlers si ya está configurado
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Formato básico para loguear por consola (Cloud Logging lo captura automáticamente)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
    return logger

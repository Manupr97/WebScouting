# logging_config.py
import logging
import sys

def configure_logging(level=logging.WARNING):
    """Configura el logging para reducir ruido"""
    
    # Formato simple
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Handler para consola
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Silenciar loggers específicos que generan mucho ruido
    noisy_loggers = [
        'models.partido_model',
        'models.jugador_model', 
        'root',
        'filelock',
        'streamlit'
    ]
    
    for logger_name in noisy_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
    
    # Para desarrollo, puedes cambiar a DEBUG temporalmente
    # logging.getLogger('models.partido_model').setLevel(logging.DEBUG)

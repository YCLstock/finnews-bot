
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Set up centralized logging for the application.
    Logs will be output to both the console and a rotating file.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file_path = os.path.join(log_dir, 'app.log')

    # Get the root logger
    logger = logging.getLogger()
    
    # Prevent adding handlers multiple times in case this function is called more than once
    if logger.hasHandlers():
        return

    logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Rotating File Handler
    # Rotates when the file reaches 2MB, keeps 5 backup files.
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=2*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

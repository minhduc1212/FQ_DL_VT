import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception:
            pass
            
    log_file = os.path.join(log_dir, "downloader.log")
    
    logger = logging.getLogger("fanqie_downloader")
    logger.setLevel(logging.DEBUG)
    
    # Tránh gắn trùng handlers khi import nhiều nơi
    if not logger.handlers:
        # Sử dụng RotatingFileHandler để giới hạn kích thước file log (5MB)
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        
        # Format log chi tiết: Thời gian - Level - [Tên file:Dòng] - Thông điệp
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
    return logger

# Tạo instance logger dùng chung cho toàn dự án
logger = setup_logger()

import sys
# Cấu hình encoding UTF-8 tránh lỗi hiển thị trên Terminal Windows
sys.stdout.reconfigure(encoding='utf-8')

from src.config import ConfigManager
from src.api import FanqieAPI
from src.downloader import NovelDownloader
from src.ui import NovelCLI
from src.logger import logger

def main():
    logger.info("=========================================")
    logger.info("Khởi động ứng dụng Fanqie Novel Downloader CLI")
    config = ConfigManager()
    api_client = FanqieAPI(timeout=config.get("timeout"))
    downloader = NovelDownloader(api_client, config)
    cli = NovelCLI(api_client, downloader, config)
    cli.run_main_loop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Ứng dụng bị dừng bằng KeyboardInterrupt (Ctrl+C) ở luồng chính.")
        print("\nĐã thoát chương trình bằng phím tắt (Ctrl+C). Tạm biệt!")
        sys.exit(0)

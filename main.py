import sys
from src.config import ConfigManager
from src.api import FanqieAPI
from src.downloader import NovelDownloader
from src.ui import NovelCLI

def main():
    config = ConfigManager()
    api_client = FanqieAPI(timeout=config.get("timeout"))
    downloader = NovelDownloader(api_client, config)
    cli = NovelCLI(api_client, downloader, config)
    cli.run_main_loop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã thoát chương trình bằng phím tắt (Ctrl+C). Tạm biệt!")
        sys.exit(0)

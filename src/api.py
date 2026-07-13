import re
import requests
import subprocess
from src.logger import logger

class FanqieAPI:
    def __init__(self, base_url="http://localhost:9999", timeout=10):
        self.base_url = base_url
        self.timeout = timeout
        logger.info(f"Initialized FanqieAPI client. Base URL: {base_url}, Timeout: {timeout}s")

    def check_connection(self):
        logger.info(f"Checking connection to FQWeb server: {self.base_url}")
        try:
            resp = requests.get(f"{self.base_url}/search?query=test&page=1", timeout=3)
            if resp.status_code == 200:
                logger.info("Connection check passed.")
                return True, "Kết nối thành công tới FQWeb API."
            else:
                logger.warning(f"Connection check returned status code: {resp.status_code}")
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
        return False, "Không thể kết nối tới server FQWeb tại http://localhost:9999"

    @staticmethod
    def run_adb_forward():
        logger.info("Executing ADB Port Forward setup...")
        try:
            res = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
            lines = res.stdout.strip().split("\n")
            devices = [line.split()[0] for line in lines[1:] if line.strip() and "device" in line]
            if not devices:
                logger.warning("ADB Forward failed: No Android devices connected via USB/WiFi.")
                return False, "Không tìm thấy thiết bị Android nào qua ADB."
            
            logger.info(f"Found active Android device: {devices[0]}. Forwarding port 9999...")
            forward_res = subprocess.run(["adb", "forward", "tcp:9999", "tcp:9999"], capture_output=True, text=True)
            if forward_res.returncode == 0:
                logger.info("ADB forward command executed successfully.")
                return True, f"Đã tự động chuyển tiếp cổng 9999 (ADB forward) từ thiết bị: {devices[0]}."
            else:
                logger.error(f"ADB forward command failed with stderr: {forward_res.stderr.strip()}")
                return False, f"Lệnh ADB forward thất bại: {forward_res.stderr.strip()}"
        except FileNotFoundError:
            logger.error("ADB tool not found on system PATH.")
            return False, "Không tìm thấy ADB trong hệ thống (PATH)."
        except Exception as e:
            logger.error(f"ADB Port Forward error: {e}")
            return False, f"Lỗi thực thi ADB: {str(e)}"

    def search_novels(self, query):
        logger.info(f"API request: searching novels for query='{query}'")
        books = []
        seen_ids = set()
        try:
            url = f"{self.base_url}/search?query={query}&page=1"
            resp = requests.get(url, timeout=self.timeout)
            logger.debug(f"Search request status code: {resp.status_code}")
            if resp.status_code == 200:
                res_json = resp.json()
                search_tabs = res_json.get("data", {}).get("search_tabs", [])
                for tab in search_tabs:
                    tab_data = tab.get("data", [])
                    for item in tab_data:
                        book_list = item.get("book_data", [])
                        for book in book_list:
                            bid = book.get("book_id")
                            if bid and bid not in seen_ids:
                                seen_ids.add(bid)
                                books.append({
                                    "id": bid,
                                    "title": book.get("book_name", "Không rõ tên"),
                                    "author": book.get("author", "Khuyết danh"),
                                    "score": book.get("score", "0.0"),
                                    "words": int(book.get("word_number")) if str(book.get("word_number", "")).strip().isdigit() else 0,
                                    "category": book.get("category", "Chưa phân loại"),
                                    "abstract": book.get("abstract", "").strip(),
                                    "sub_info": book.get("sub_info", "")
                                })
                logger.info(f"API success: found {len(books)} books matching query.")
        except Exception as e:
            logger.error(f"Error during novel search API call: {e}")
        return books

    def get_book_info(self, book_id):
        logger.info(f"API request: fetching book details for book_id={book_id}")
        try:
            url = f"{self.base_url}/info?book_id={book_id}"
            resp = requests.get(url, timeout=self.timeout)
            logger.debug(f"Book info status code: {resp.status_code}")
            if resp.status_code == 200:
                res_json = resp.json()
                if res_json.get("isSuccess"):
                    data_wrap = res_json.get("data", {})
                    if isinstance(data_wrap, dict):
                        logger.info("Book info fetched successfully.")
                        return data_wrap.get("data", {})
                else:
                    logger.warning(f"Book info API returned isSuccess=False. Msg: {res_json.get('errorMsg')}")
        except Exception as e:
            logger.error(f"Error fetching book info for ID {book_id}: {e}")
        return None

    def get_catalog(self, book_id):
        logger.info(f"API request: fetching chapter catalog for book_id={book_id}")
        try:
            url = f"{self.base_url}/catalog?book_id={book_id}"
            resp = requests.get(url, timeout=self.timeout)
            logger.debug(f"Catalog status code: {resp.status_code}")
            if resp.status_code == 200:
                res_json = resp.json()
                data_wrap = res_json.get("data", {})
                if res_json.get("isSuccess") or (isinstance(data_wrap, dict) and data_wrap.get("code") == "0"):
                    if isinstance(data_wrap, dict):
                        catalog_data = data_wrap.get("data", {})
                        logger.info(f"Catalog fetched successfully. Found {len(catalog_data.get('catalog_data', []))} chapters.")
                        return catalog_data
                else:
                    logger.warning(f"Catalog API returned failure. Msg: {res_json.get('errorMsg')}")
        except Exception as e:
            logger.error(f"Error fetching catalog for book_id {book_id}: {e}")
        return None

    def get_category_books(self, category_id):
        logger.info(f"API request: listing books for category_id={category_id}")
        books = []
        params = {
            "category_id": str(category_id),
            "limit": "20",
            "offset": "0",
            "gender": "1",
            "aid": "1967",
            "app_name": "novelapp",
            "version_code": "50803"
        }
        try:
            url = f"{self.base_url}/reading/bookapi/new_category/landing/v/"
            resp = requests.get(url, params=params, timeout=self.timeout)
            logger.debug(f"Category status code: {resp.status_code}")
            if resp.status_code == 200:
                res_json = resp.json()
                book_info_list = res_json.get("data", {}).get("data", {}).get("book_info", [])
                for book in book_info_list:
                    bid = book.get("book_id")
                    if bid:
                        books.append({
                            "id": bid,
                            "title": book.get("book_name", "Không rõ tên"),
                            "author": book.get("author", "Khuyết danh"),
                            "score": book.get("score", "0.0"),
                            "words": int(book.get("word_number")) if str(book.get("word_number", "")).strip().isdigit() else 0,
                            "category": book.get("category", "Chưa phân loại"),
                            "abstract": book.get("abstract", "").strip(),
                            "sub_info": book.get("sub_info", "")
                        })
                logger.info(f"Fetched {len(books)} books for category {category_id}.")
        except Exception as e:
            logger.error(f"Error fetching category books: {e}")
        return books

    def get_chapter_content(self, item_id):
        logger.debug(f"API request: fetching content for chapter item_id={item_id}")
        url = f"{self.base_url}/content?item_id={item_id}"
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                res_json = resp.json()
                data_wrap = res_json.get("data", {})
                if isinstance(data_wrap, str):
                    logger.error(f"FQWeb returned Stacktrace Error for item_id={item_id}: {data_wrap[:150]}...")
                    return {"error": data_wrap}
                if res_json.get("isSuccess") or (isinstance(data_wrap, dict) and data_wrap.get("code") == 0):
                    if isinstance(data_wrap, dict):
                        logger.debug(f"Successfully fetched content for item_id={item_id}.")
                        return data_wrap.get("data", {})
            else:
                logger.warning(f"Chapter content endpoint returned HTTP {resp.status_code} for item_id={item_id}")
        except Exception as e:
            logger.error(f"Exception fetching content for item_id {item_id}: {e}")
        return None

    @staticmethod
    def extract_id_from_url(url):
        match = re.search(r'\d{19}', url)
        if match:
            return match.group(0)
        match2 = re.search(r'\d{15,22}', url)
        if match2:
            return match2.group(0)
        return None

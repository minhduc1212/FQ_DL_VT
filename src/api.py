import re
import requests
import subprocess

class FanqieAPI:
    def __init__(self, base_url="http://localhost:9999", timeout=10):
        self.base_url = base_url
        self.timeout = timeout

    def check_connection(self):
        try:
            resp = requests.get(f"{self.base_url}/search?query=test&page=1", timeout=3)
            if resp.status_code == 200:
                return True, "Kết nối thành công tới FQWeb API."
        except Exception:
            pass
        return False, "Không thể kết nối tới server FQWeb tại http://localhost:9999"

    @staticmethod
    def run_adb_forward():
        try:
            res = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
            lines = res.stdout.strip().split("\n")
            devices = [line.split()[0] for line in lines[1:] if line.strip() and "device" in line]
            if not devices:
                return False, "Không tìm thấy thiết bị Android nào qua ADB."
            forward_res = subprocess.run(["adb", "forward", "tcp:9999", "tcp:9999"], capture_output=True, text=True)
            if forward_res.returncode == 0:
                return True, f"Đã tự động chuyển tiếp cổng 9999 (ADB forward) từ thiết bị: {devices[0]}."
            else:
                return False, f"Lệnh ADB forward thất bại: {forward_res.stderr.strip()}"
        except FileNotFoundError:
            return False, "Không tìm thấy ADB trong hệ thống (PATH)."
        except Exception as e:
            return False, f"Lỗi thực thi ADB: {str(e)}"

    def search_novels(self, query):
        books = []
        seen_ids = set()
        try:
            url = f"{self.base_url}/search?query={query}&page=1"
            resp = requests.get(url, timeout=self.timeout)
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
        except Exception:
            pass
        return books

    def get_book_info(self, book_id):
        try:
            url = f"{self.base_url}/info?book_id={book_id}"
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                res_json = resp.json()
                if res_json.get("isSuccess"):
                    data_wrap = res_json.get("data", {})
                    if isinstance(data_wrap, dict):
                        return data_wrap.get("data", {})
        except Exception:
            pass
        return None

    def get_catalog(self, book_id):
        try:
            url = f"{self.base_url}/catalog?book_id={book_id}"
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                res_json = resp.json()
                data_wrap = res_json.get("data", {})
                if res_json.get("isSuccess") or (isinstance(data_wrap, dict) and data_wrap.get("code") == "0"):
                    if isinstance(data_wrap, dict):
                        return data_wrap.get("data", {})
        except Exception:
            pass
        return None

    def get_category_books(self, category_id):
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
        except Exception:
            pass
        return books

    def get_chapter_content(self, item_id):
        url = f"{self.base_url}/content?item_id={item_id}"
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                res_json = resp.json()
                data_wrap = res_json.get("data", {})
                if isinstance(data_wrap, str):
                    return {"error": data_wrap}
                if res_json.get("isSuccess") or (isinstance(data_wrap, dict) and data_wrap.get("code") == 0):
                    if isinstance(data_wrap, dict):
                        return data_wrap.get("data", {})
        except Exception:
            pass
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

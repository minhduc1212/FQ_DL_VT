import time
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
import questionary
from src.logger import logger

class NovelCLI:
    CATEGORIES = [
        {"name": "Huyền Huyễn Não Động (玄幻脑洞)", "id": 257},
        {"name": "Huyền Huyễn (玄幻)", "id": 7},
        {"name": "Đô Thị Não Động (都市脑洞)", "id": 256},
        {"name": "Đô Thị (都市)", "id": 6},
        {"name": "Xuyên Không (穿越)", "id": 37},
        {"name": "Hệ Thống (系统)", "id": 19},
        {"name": "Vô Địch (无敌)", "id": 384},
        {"name": "Trùng Sinh (重生)", "id": 36},
        {"name": "Khởi Đầu (开局)", "id": 453},
        {"name": "Phản Phái (反派)", "id": 369},
        {"name": "Khoa Huyện (科幻)", "id": 9},
        {"name": "Võ Hiệp (武侠)", "id": 16},
        {"name": "Tiên Hiệp (仙侠)", "id": 15},
        {"name": "Lịch Sử (历史)", "id": 11},
        {"name": "Nghịch Thiên Cải Mệnh (逆天改命)", "id": 966},
    ]

    def __init__(self, api_client, downloader, config_manager):
        self.api = api_client
        self.downloader = downloader
        self.config = config_manager
        self.console = Console()
        logger.info("Initialized NovelCLI.")

    def print_banner(self):
        self.console.clear()
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]   [bold green]🍅 TRÌNH TẢI TRUYỆN FANQIE NOVEL CLI (CUSTOM CLIENT)[/bold green]                  [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]   [bold yellow]Phiên bản 1.0.0 | Kết nối thông qua FQWeb Local API[/bold yellow]                [bold cyan]║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════════════╝[/bold cyan]
"""
        self.console.print(banner)

    def search_menu(self, search_by="title"):
        self.print_banner()
        type_str = "Tên truyện" if search_by == "title" else "Tên tác giả"
        query = questionary.text(f"Nhập {type_str} cần tìm:").ask()
        
        if not query or not query.strip():
            return
            
        query = query.strip()
        logger.info(f"User search action: search_by={search_by}, query='{query}'")
        
        with self.console.status(f"[bold cyan]Đang tìm kiếm truyện theo {type_str.lower()}...[/bold cyan]"):
            results = self.api.search_novels(query)

        if not results:
            logger.info("No search results found.")
            self.console.print(f"[bold red]Không tìm thấy kết quả nào phù hợp với '{query}'.[/bold red]")
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()
            return

        # Lọc kết quả nếu tìm theo tác giả
        filtered_results = []
        if search_by == "author":
            for book in results:
                if query.lower() in book["author"].lower():
                    filtered_results.append(book)
            if not filtered_results:
                logger.info("No search results match author name filters.")
                self.console.print(f"[bold red]Tìm thấy truyện chứa từ khóa nhưng không có tác giả nào khớp hoàn toàn với '{query}'.[/bold red]")
                questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()
                return
            results = filtered_results

        logger.info(f"Displaying {len(results)} search results.")
        self.print_banner()
        self.console.print(f"[bold green]KẾT QUẢ TÌM KIẾM CHO '{query}':[/bold green]\n")
        
        choices = []
        for idx, book in enumerate(results):
            info_str = f"{idx + 1}. [Tên] {book['title']} - [Tác giả] {book['author']} | [Từ] {book['words']:,} từ | [Điểm] {book['score']}★"
            choices.append(info_str)
        choices.append("⬅️ Quay lại Menu chính")

        selection = questionary.select("Chọn truyện để xem chi tiết & tải:", choices=choices).ask()
        
        if selection == "⬅️ Quay lại Menu chính" or selection is None:
            return
            
        selected_idx = int(selection.split(".")[0]) - 1
        selected_book = results[selected_idx]
        
        logger.info(f"Selected book: {selected_book['title']} ({selected_book['id']})")
        self.downloader.download_novel(selected_book["id"])

    def browse_discovery_menu(self):
        self.print_banner()
        self.console.print("[bold green]KHÁM PHÁ THEO THỂ LOẠI (DISCOVERY)[/bold green]\n")
        
        choices = [cat["name"] for cat in self.CATEGORIES]
        choices.append("⬅️ Quay lại Menu chính")
        
        selection = questionary.select("Chọn thể loại truyện cần xem:", choices=choices).ask()
        
        if selection == "⬅️ Quay lại Menu chính" or selection is None:
            return
            
        selected_cat = next(cat for cat in self.CATEGORIES if cat["name"] == selection)
        logger.info(f"User browsing category: {selected_cat['name']} (ID: {selected_cat['id']})")
        
        with self.console.status("[bold cyan]Đang tải danh sách truyện nổi bật...[/bold cyan]"):
            books = self.api.get_category_books(selected_cat["id"])

        if not books:
            logger.warning(f"Failed to fetch books for category {selected_cat['name']}.")
            self.console.print("[bold red]Lỗi: Không lấy được danh sách truyện của thể loại này.[/bold red]")
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()
            return

        self.print_banner()
        self.console.print(f"[bold green]TRUYỆN NỔI BẬT - {selected_cat['name']}:[/bold green]\n")
        
        book_choices = []
        for idx, book in enumerate(books):
            info_str = f"{idx + 1}. {book['title']} - {book['author']} | [Từ] {book['words']:,} từ | {book['score']}★"
            book_choices.append(info_str)
        book_choices.append("⬅️ Quay lại Menu chính")

        book_sel = questionary.select("Chọn truyện để tải hoặc xem chi tiết:", choices=book_choices).ask()
        
        if book_sel == "⬅️ Quay lại Menu chính" or book_sel is None:
            return
            
        selected_idx = int(book_sel.split(".")[0]) - 1
        selected_book = books[selected_idx]
        
        logger.info(f"Selected category book: {selected_book['title']} ({selected_book['id']})")
        self.downloader.download_novel(selected_book["id"])

    def download_by_id_menu(self):
        self.print_banner()
        self.console.print("[bold green]TẢI TRUYỆN BẰNG ID[/bold green]\n")
        book_id = questionary.text("Nhập ID truyện cần tải (Ví dụ: 7484611801053678654):").ask()
        
        if book_id and book_id.strip():
            book_id = book_id.strip()
            if book_id.isdigit():
                logger.info(f"User action: download by manual ID: {book_id}")
                self.downloader.download_novel(book_id)
            else:
                self.console.print("[bold red]Lỗi: ID truyện phải là một dãy số nguyên.[/bold red]")
                questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()

    def download_by_url_menu(self):
        self.print_banner()
        self.console.print("[bold green]TẢI TRUYỆN BẰNG LINK / URL[/bold green]\n")
        url = questionary.text("Dán URL trang chi tiết truyện (ví dụ link fanqie):").ask()
        
        if url and url.strip():
            url = url.strip()
            book_id = self.api.extract_id_from_url(url)
            if book_id:
                logger.info(f"User action: download by URL={url}. Extracted ID={book_id}")
                self.console.print(f"[green]Đã trích xuất được ID truyện:[/green] [bold cyan]{book_id}[/bold cyan]")
                time.sleep(1)
                self.downloader.download_novel(book_id)
            else:
                logger.warning(f"Could not extract book ID from URL: {url}")
                self.console.print("[bold red]Lỗi: Không tìm thấy ID truyện hợp lệ (19 chữ số) trong URL đã nhập.[/bold red]")
                questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()

    def settings_menu(self):
        while True:
            self.print_banner()
            concurrency = self.config.get('concurrency')
            mode_text = "(Tải tuần tự/Lần lượt)" if concurrency == 1 else "(Tải đa luồng)"
            self.console.print(Panel(
                f"[bold green]CÀI ĐẶT HIỆN TẠI[/bold green]\n\n"
                f"[bold yellow]1. Số luồng tải đồng thời (Concurrency):[/bold yellow] {concurrency} luồng [dim]{mode_text}[/dim]\n"
                f"[bold yellow]2. Thời gian trễ giữa các chương (Delay):[/bold yellow] {self.config.get('request_delay')} giây\n"
                f"[bold yellow]3. Số lần tải lại khi lỗi (Retry attempts):[/bold yellow] {self.config.get('retry_attempts')} lần\n"
                f"[bold yellow]4. Thời gian chờ tối đa (Timeout):[/bold yellow] {self.config.get('timeout')} giây\n"
                f"[bold yellow]5. Thư mục lưu truyện (Save dir):[/bold yellow] {self.config.get('download_dir')}\n"
                f"[bold yellow]6. Định dạng lưu trữ (Format):[/bold yellow] {self.config.get('save_format')}",
                border_style="cyan"
            ))
            
            setting_choices = [
                "1. Thay đổi số luồng tải đồng thời (Chọn 1 để tải lần lượt)",
                "2. Thay đổi thời gian trễ giữa các chương",
                "3. Thay đổi số lần tải lại khi lỗi",
                "4. Thay đổi thời gian chờ tối đa (timeout)",
                "5. Thay đổi thư mục lưu truyện",
                "6. Thay đổi định dạng lưu trữ (File gộp hoặc chia nhỏ)",
                "⬅️ Quay lại Menu chính"
              ]
            
            choice = questionary.select("Chọn mục cài đặt cần thay đổi:", choices=setting_choices).ask()
            
            if choice == "⬅️ Quay lại Menu chính" or choice is None:
                break
            elif choice.startswith("1."):
                val = questionary.text(
                    "Nhập số luồng tải (1 - 20, chọn 1 để tải lần lượt):", 
                    default=str(self.config.get("concurrency"))
                ).ask()
                if val and val.isdigit():
                    self.config.set("concurrency", max(1, min(20, int(val))))
            elif choice.startswith("2."):
                val = questionary.text(
                    "Nhập thời gian trễ (giây, ví dụ 0.3 hoặc 0.5):", 
                    default=str(self.config.get("request_delay"))
                ).ask()
                if val:
                    try:
                        self.config.set("request_delay", max(0.0, min(10.0, float(val))))
                    except ValueError:
                        pass
            elif choice.startswith("3."):
                val = questionary.text(
                    "Nhập số lần tải lại khi lỗi (1 - 10):", 
                    default=str(self.config.get("retry_attempts"))
                ).ask()
                if val and val.isdigit():
                    self.config.set("retry_attempts", max(1, min(10, int(val))))
            elif choice.startswith("4."):
                val = questionary.text(
                    "Nhập thời gian chờ tối đa (giây, 3 - 60):", 
                    default=str(self.config.get("timeout"))
                ).ask()
                if val and val.isdigit():
                    self.config.set("timeout", max(3, min(60, int(val))))
            elif choice.startswith("5."):
                val = questionary.text(
                    "Nhập thư mục lưu truyện:", 
                    default=self.config.get("download_dir")
                ).ask()
                if val and val.strip():
                    self.config.set("download_dir", val.strip())
            elif choice.startswith("6."):
                fmt = questionary.select(
                    "Chọn định dạng lưu trữ:",
                    choices=["Một file TXT duy nhất", "Chia nhỏ từng chương"]
                ).ask()
                if fmt:
                    self.config.set("save_format", fmt)

    def view_log_file(self):
        self.print_banner()
        log_file = os.path.join("logs", "downloader.log")
        logger.info("User action: viewing log file from CLI.")
        
        if not os.path.exists(log_file):
            self.console.print("[yellow]Chưa có file nhật ký hoạt động nào được tạo.[/yellow]")
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()
            return
            
        self.console.print("\n[bold cyan]🔍 30 DÒNG NHẬT KÝ HOẠT ĐỘNG GẦN NHẤT:[/bold cyan]\n")
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                last_lines = lines[-30:]
                for line in last_lines:
                    self.console.print(line.strip(), highlight=False)
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            self.console.print(f"[bold red]Lỗi khi đọc file log: {e}[/bold red]")
            
        self.console.print("\n[bold cyan]----------------------------------------------------------------------[/bold cyan]\n")
        questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()

    def run_main_loop(self):
        logger.info("=== Starting Main Loop ===")
        self.print_banner()
        self.console.print("[cyan]Đang kiểm tra kết nối tới server FQWeb (http://localhost:9999)...[/cyan]")
        
        connected, msg = self.api.check_connection()
        if not connected:
            self.console.print("[yellow]Cảnh báo: Không kết nối được tới cổng 9999. Đang thử tự động thiết lập ADB Port Forward...[/yellow]")
            success, forward_msg = self.api.run_adb_forward()
            if success:
                self.console.print(f"[green]✓ {forward_msg}[/green]")
                time.sleep(1)
                connected, msg = self.api.check_connection()
            else:
                self.console.print(f"[red]✗ {forward_msg}[/red]")
                time.sleep(1)
                
        if not connected:
            logger.warning("Starting CLI in OFFLINE mode (unable to connect to FQWeb server).")
            self.console.print(Panel(
                "[bold red]❌ KHÔNG THỂ KẾT NỐI TỚI SERVER FQWEB[/bold red]\n\n"
                "Ứng dụng yêu cầu app Fanqie Novel (có cài mô-đun Xposed FQWeb) đang chạy trên điện thoại hoặc giả lập Android.\n\n"
                "[bold yellow]Hướng dẫn khắc phục:[/bold yellow]\n"
                "1. Bật điện thoại/giả lập Android của bạn lên.\n"
                "2. Mở app [bold green]番茄小说 (Fanqie Novel)[/bold green], vào Cài đặt -> bật Web API.\n"
                "3. Chạy lệnh sau trên máy tính để chuyển tiếp cổng:\n"
                "   [cyan]adb forward tcp:9999 tcp:9999[/cyan]\n\n"
                "[dim]Bạn có muốn tiếp tục chạy thử ở chế độ Offline? (Một số tính năng mạng sẽ lỗi)[/dim]",
                title="Lỗi Kết Nối Cổng 9999",
                border_style="red"
            ))
            cont = questionary.confirm("Tiếp tục chạy ứng dụng?", default=True).ask()
            if not cont:
                logger.info("Application exited because FQWeb server is offline.")
                sys.exit(0)
        else:
            self.console.print("[bold green]✓ Đã kết nối thành công tới FQWeb Local API Server![/bold green]")
            time.sleep(1)

        while True:
            self.print_banner()
            menu_choices = [
                "🔍 Tìm kiếm truyện theo Tên (Search by Title)",
                "👤 Tìm kiếm truyện theo Tác giả (Search by Author)",
                "🧭 Khám phá truyện theo Thể loại (Browse Category)",
                "🆔 Tải truyện bằng ID (Download by ID)",
                "🔗 Tải truyện bằng URL/Link (Download by URL)",
                "📋 Xem Nhật Ký Hoạt Động (View Log File)",
                "⚙️ Cấu hình cài đặt (Settings)",
                "❌ Thoát chương trình (Exit)"
            ]
            
            choice = questionary.select(
                "Chọn chức năng cần thực hiện:",
                choices=menu_choices
            ).ask()
            
            if choice is None or choice.startswith("❌"):
                logger.info("User selected exit. App terminating.")
                self.console.print("[cyan]Cảm ơn bạn đã sử dụng trình tải truyện! Tạm biệt![/cyan]")
                sys.exit(0)
            elif choice.startswith("🔍"):
                self.search_menu(search_by="title")
            elif choice.startswith("👤"):
                self.search_menu(search_by="author")
            elif choice.startswith("🧭"):
                self.browse_discovery_menu()
            elif choice.startswith("🆔"):
                self.download_by_id_menu()
            elif choice.startswith("🔗"):
                self.download_by_url_menu()
            elif choice.startswith("📋"):
                self.view_log_file()
            elif choice.startswith("⚙️"):
                self.settings_menu()

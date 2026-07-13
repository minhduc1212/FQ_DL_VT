import time
import sys
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
import questionary

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
        {"name": "Khoa Huyễn (科幻)", "id": 9},
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

    def print_banner(self):
        self.console.clear()
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]   [bold green]🍅 TRÌNH TẢI TRUYỆN FANQIE NOVEL CLI (CUSTOM CLIENT)[/bold green]                  [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]   [bold yellow]Phiên bản 1.0.0 | Kết nối thông qua FQWeb Local API[/bold yellow]                [bold cyan]║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════════════╝[/bold cyan]
"""
        self.console.print(Align.center(banner))

    def show_detail_and_confirm(self, book):
        self.print_banner()
        self.console.print(Panel(
            f"[bold yellow]Tiêu đề truyện:[/bold yellow] [bold green]{book['title']}[/bold green]\n"
            f"[bold yellow]ID truyện:[/bold yellow] [bold cyan]{book['id']}[/bold cyan]\n"
            f"[bold yellow]Tác giả:[/bold yellow] [bold white]{book['author']}[/bold white]\n"
            f"[bold yellow]Điểm số:[/bold yellow] {book['score']}★\n"
            f"[bold yellow]Phân loại:[/bold yellow] {book['category']} | {book['sub_info']}\n"
            f"[bold yellow]Số chữ:[/bold yellow] {book['words']:,} từ\n\n"
            f"[bold yellow]Tóm tắt truyện:[/bold yellow]\n{book['abstract']}",
            title="[bold green]CHI TIẾT TRUYỆN[/bold green]",
            border_style="cyan"
        ))
        
        choice = questionary.confirm("Bạn có muốn tải bộ truyện này không?", default=True).ask()
        if choice:
            self.downloader.download_novel(book['id'])

    def search_menu(self, search_by="title"):
        self.print_banner()
        prompt = "Nhập tên truyện cần tìm: " if search_by == "title" else "Nhập tên tác giả cần tìm: "
        query = questionary.text(prompt).ask()
        
        if not query or not query.strip():
            return
            
        books = []
        with self.console.status(f"[bold cyan]Đang tìm kiếm theo {('tên truyện' if search_by == 'title' else 'tác giả')}...[/bold cyan]"):
            books = self.api.search_novels(query.strip())
            
        if not books:
            self.console.print("[yellow]Không tìm thấy kết quả phù hợp nào.[/yellow]")
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để quay lại menu...").ask()
            return
            
        options = []
        for idx, b in enumerate(books):
            opt_text = f"{idx+1}. {b['title']} - Tác giả: {b['author']} ({b['category']} | {b['score']}★ | {b['sub_info']})"
            options.append(questionary.Choice(opt_text, value=b))
            
        options.append(questionary.Choice("⬅️ Quay lại Menu chính", value="back"))
        
        choice = questionary.select(
            "Chọn truyện để xem chi tiết và tải xuống:",
            choices=options,
            use_shortcut_keys=True
        ).ask()
        
        if choice != "back":
            self.show_detail_and_confirm(choice)

    def browse_discovery_menu(self):
        self.print_banner()
        options = [questionary.Choice(cat["name"], value=cat) for cat in self.CATEGORIES]
        options.append(questionary.Choice("⬅️ Quay lại Menu chính", value="back"))
        
        cat_choice = questionary.select(
            "Chọn thể loại để khám phá:",
            choices=options
        ).ask()
        
        if cat_choice == "back":
            return
            
        books = []
        with self.console.status(f"[bold cyan]Đang tải danh sách truyện thuộc thể loại {cat_choice['name']}...[/bold cyan]"):
            books = self.api.get_category_books(cat_choice["id"])
            
        if not books:
            self.console.print("[yellow]Không lấy được dữ liệu thể loại từ server (Cần bật app FQWeb).[/yellow]")
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để quay lại...").ask()
            return
            
        book_options = []
        for idx, b in enumerate(books):
            opt_text = f"{idx+1}. {b['title']} - Tác giả: {b['author']} ({b['score']}★ | {b['sub_info']})"
            book_options.append(questionary.Choice(opt_text, value=b))
            
        book_options.append(questionary.Choice("⬅️ Quay lại", value="back"))
        
        choice = questionary.select(
            f"Danh sách truyện nổi bật của {cat_choice['name']}:",
            choices=book_options
        ).ask()
        
        if choice != "back":
            self.show_detail_and_confirm(choice)

    def download_by_id_menu(self):
        self.print_banner()
        book_id = questionary.text("Nhập ID truyện cần tải (Ví dụ: 7484611801053678654):").ask()
        if book_id and book_id.strip():
            if book_id.strip().isdigit():
                self.downloader.download_novel(book_id.strip())
            else:
                self.console.print("[red]ID truyện phải là một dãy số nguyên.[/red]")
                questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()

    def download_by_url_menu(self):
        self.print_banner()
        url = questionary.text(
            "Nhập Link/URL truyện Fanqie:\n"
            "(Ví dụ: https://fanqie.com/reader/7484611801053678654 hoặc từ giao diện chia sẻ)"
        ).ask()
        if url and url.strip():
            book_id = self.api.extract_id_from_url(url.strip())
            if book_id:
                self.console.print(f"[green]Đã trích xuất được ID truyện:[/green] [bold cyan]{book_id}[/bold cyan]")
                time.sleep(1)
                self.downloader.download_novel(book_id)
            else:
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
            
            if choice == "⬅️ Quay lại Menu chính":
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

    def run_main_loop(self):
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
                "⚙️ Cấu hình cài đặt (Settings)",
                "❌ Thoát chương trình (Exit)"
            ]
            
            choice = questionary.select(
                "Chọn chức năng cần thực hiện:",
                choices=menu_choices
            ).ask()
            
            if choice is None or choice.startswith("❌"):
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
            elif choice.startswith("⚙️"):
                self.settings_menu()

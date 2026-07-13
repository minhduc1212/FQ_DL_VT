import os
import re
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
import questionary
from src.logger import logger

class NovelDownloader:
    def __init__(self, api_client, config_manager):
        self.api = api_client
        self.config = config_manager
        self.console = Console()
        self.restarting_event = threading.Event()
        self.restarting_event.set()
        self.consecutive_failures = 0
        logger.info("Initialized NovelDownloader.")

    @staticmethod
    def safe_filename(name):
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()

    @staticmethod
    def clean_content(text):
        if not text:
            return ""
        if "<p" in text or "<br" in text or "<html>" in text:
            text = re.sub(r'</p>\s*<p[^>]*>', '\n\n', text)
            text = re.sub(r'<p[^>]*>', '', text)
            text = re.sub(r'</p>', '\n\n', text)
            text = re.sub(r'<br\s*/?>', '\n', text)
            text = re.sub(r'<[^>]+>', '', text)
        
        import html
        text = html.unescape(text)
        
        lines = []
        for line in text.split("\n"):
            line_str = line.strip()
            if line_str:
                lines.append("    " + line_str)
            else:
                lines.append("")
        
        cleaned = "\n".join(lines)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    def load_temp_chapter(self, temp_file):
        if os.path.exists(temp_file):
            try:
                with open(temp_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "title" in data and "content" in data:
                        return data
            except Exception as e:
                logger.error(f"Failed to load or parse temp file {temp_file}: {e}. Removing file.")
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
        return None

    def get_missing_count(self, temp_dir, total_chapters):
        missing = 0
        for idx in range(total_chapters):
            if not os.path.exists(os.path.join(temp_dir, f"{idx}.json")):
                missing += 1
        return missing

    def get_completed_count(self, temp_dir, total_chapters):
        completed = 0
        for idx in range(total_chapters):
            if os.path.exists(os.path.join(temp_dir, f"{idx}.json")):
                completed += 1
        return completed

    def get_final_path(self, out_dir, title, author):
        title_safe = self.safe_filename(title)
        author_safe = self.safe_filename(author)
        save_format = self.config.get("save_format")
        if save_format == "Một file TXT duy nhất":
            return os.path.join(out_dir, f"{title_safe} - {author_safe}.txt")
        else:
            return os.path.join(out_dir, f"{title_safe} - {author_safe}")

    def clean_temp_dir(self, temp_dir):
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        try:
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
            logger.info("Temporary directory cleaned successfully.")
        except Exception as e:
            logger.error(f"Error cleaning temporary directory: {e}")

    def restart_fanqie_app(self):
        self.restarting_event.clear()
        logger.warning("Triggered auto-restart: 15 consecutive download failures detected.")
        self.console.print("\n[yellow]⚠️ Phát hiện lỗi liên tiếp. Đang tự động khởi động lại ứng dụng Fanqie Novel để giải phóng RAM...[/yellow]")
        try:
            import subprocess
            # Force stop the app
            logger.info("Executing: adb shell am force-stop com.dragon.read")
            subprocess.run(["adb", "shell", "am", "force-stop", "com.dragon.read"], capture_output=True, timeout=5)
            time.sleep(2)
            # Launch the app
            logger.info("Executing: adb shell monkey -p com.dragon.read 1")
            subprocess.run(["adb", "shell", "monkey", "-p", "com.dragon.read", "1"], capture_output=True, timeout=5)
            time.sleep(3)
            # Re-establish port forward
            logger.info("Executing: adb forward tcp:9999 tcp:9999")
            subprocess.run(["adb", "forward", "tcp:9999", "tcp:9999"], capture_output=True, timeout=5)
            
            # Active polling loop: Chờ cho tới khi FQWeb server Online thực sự
            logger.info("Waiting for FQWeb API server to respond online...")
            server_online = False
            for attempt in range(30):
                connected, _ = self.api.check_connection()
                if connected:
                    server_online = True
                    logger.info(f"Server is verified ONLINE after {attempt+1} seconds.")
                    break
                logger.debug(f"Server not ready (attempt {attempt+1}/30), waiting 1s...")
                time.sleep(1)
                
            if server_online:
                self.console.print("[green]✓ Khởi động lại thành công và Server đã Sẵn Sàng! Tiếp tục tải...[/green]")
                self.consecutive_failures = 0
            else:
                logger.error("Server failed to come online after 30 seconds.")
                self.console.print("[bold red]⚠️ Cảnh báo: Đã khởi động lại app nhưng Server FQWeb chưa phản hồi. Tiếp tục tiến trình...[/bold red]")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error during ADB app restart: {e}")
            self.console.print(f"[bold red]Lỗi tự động khởi động lại ADB: {e}[/bold red]")
        finally:
            self.restarting_event.set()

    def compile_output(self, temp_dir, out_dir, title, author, abstract, catalog_list):
        title_safe = self.safe_filename(title)
        author_safe = self.safe_filename(author)
        save_format = self.config.get("save_format")
        logger.info(f"Compiling downloaded chapters into format: {save_format}")
        
        if save_format == "Một file TXT duy nhất":
            file_path = os.path.join(out_dir, f"{title_safe} - {author_safe}.txt")
            logger.info(f"Writing single consolidated TXT file: {file_path}")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"====================================================\n")
                    f.write(f"TÊN TRUYỆN: {title}\n")
                    f.write(f"TÁC GIẢ: {author}\n")
                    f.write(f"TỔNG SỐ CHƯƠNG: {len(catalog_list)}\n")
                    f.write(f"TẢI XUỐNG NGÀY: {time.strftime('%d/%m/%Y %H:%M:%S')}\n")
                    if abstract:
                        f.write(f"TÓM TẮT:\n{abstract}\n")
                    f.write(f"====================================================\n\n\n")
                    
                    for idx, ch_info in enumerate(catalog_list):
                        temp_file = os.path.join(temp_dir, f"{idx}.json")
                        chapter_data = self.load_temp_chapter(temp_file)
                        
                        f.write(f"====================================================\n")
                        if chapter_data:
                            ch_title = chapter_data["title"]
                            ch_text = chapter_data["content"]
                            cleaned_text = self.clean_content(ch_text)
                            f.write(f"{ch_title}\n")
                            f.write(f"====================================================\n\n")
                            f.write(cleaned_text)
                        else:
                            ch_orig_title = ch_info.get("catalog_title")
                            f.write(f"{ch_orig_title} (CHƯA TẢI/LỖI)\n")
                            f.write(f"====================================================\n\n")
                            f.write("[Nội dung chương này chưa được tải xuống hoặc bị lỗi. Hãy chạy lại app để tải tiếp.]\n")
                        f.write("\n\n\n")
                logger.info("Single TXT file compiled successfully.")
            except Exception as e:
                logger.error(f"Error compiling single TXT file: {e}")
                self.console.print(f"[bold red]Lỗi khi ghi file gộp: {e}[/bold red]")
        else:
            folder_path = os.path.join(out_dir, f"{title_safe} - {author_safe}")
            logger.info(f"Writing separate chapter text files to folder: {folder_path}")
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            try:
                for idx, ch_info in enumerate(catalog_list):
                    pad_idx = str(idx + 1).zfill(4)
                    ch_orig_title = ch_info.get("catalog_title")
                    ch_orig_title_safe = self.safe_filename(ch_orig_title)
                    file_name = f"{pad_idx}_{ch_orig_title_safe}.txt"
                    file_path = os.path.join(folder_path, file_name)
                    
                    temp_file = os.path.join(temp_dir, f"{idx}.json")
                    chapter_data = self.load_temp_chapter(temp_file)
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        if chapter_data:
                            ch_title = chapter_data["title"]
                            ch_text = chapter_data["content"]
                            cleaned_text = self.clean_content(ch_text)
                            f.write(f"{ch_title}\n\n")
                            f.write(cleaned_text)
                        else:
                            f.write(f"{ch_orig_title} (CHƯA TẢI/LỖI)\n\n")
                            f.write("[Nội dung chương này chưa được tải xuống hoặc bị lỗi. Hãy chạy lại app để tải tiếp.]")
                logger.info("Separate chapter files written successfully.")
            except Exception as e:
                logger.error(f"Error writing separate files: {e}")
                self.console.print(f"[bold red]Lỗi khi ghi các file nhỏ: {e}[/bold red]")

    def download_chapter_task(self, item_id, catalog_title, index, temp_file, retry_count):
        # Wait if restart is in progress
        self.restarting_event.wait()

        concurrency = self.config.get("concurrency")
        if concurrency > 1:
            # Stagger threads when starting
            time.sleep((index % concurrency) * 0.05)

        logger.debug(f"Thread task started: index={index}, title='{catalog_title}'")
        for attempt in range(retry_count):
            try:
                content_data = self.api.get_chapter_content(item_id)
                if content_data:
                    if isinstance(content_data, dict) and "error" in content_data:
                        logger.error(f"Chapter index={index} API error response: {content_data.get('error')[:150]}")
                        return index, catalog_title, False
                    text = content_data.get("content", "")
                    title = content_data.get("title", catalog_title)
                    if text:
                        # Write to temp file immediately (save as you go)
                        with open(temp_file, "w", encoding="utf-8") as f:
                            json.dump({"title": title, "content": text}, f, ensure_ascii=False, indent=2)
                        
                        logger.debug(f"Chapter index={index} saved successfully. Size: {len(text)} chars.")
                        
                        # Apply regular request delay to prevent hammering FQWeb
                        delay = self.config.get("request_delay")
                        if delay > 0:
                            time.sleep(delay)
                        return index, title, True
                logger.warning(f"Chapter index={index} empty response (attempt {attempt+1}/{retry_count})")
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Chapter index={index} exception on attempt {attempt+1}/{retry_count}: {e}")
                time.sleep(0.5)
        logger.error(f"Chapter index={index} failed permanently after {retry_count} attempts.")
        return index, catalog_title, False

    def download_novel(self, book_id, interactive=True):
        logger.info(f"=== Starting Download Flow for Book ID: {book_id} ===")
        info = None
        catalog_list = []
        
        with self.console.status("[bold cyan]Đang truy vấn thông tin chi tiết và mục lục...[/bold cyan]"):
            info = self.api.get_book_info(book_id)
            catalog_data = self.api.get_catalog(book_id)
            if catalog_data:
                catalog_list = catalog_data.get("catalog_data", [])
                if not info:
                    info = catalog_data.get("book_info", {})

        if not catalog_list:
            logger.error("Download failed: empty chapter list/catalog from FQWeb.")
            self.console.print("[bold red]Lỗi: Không lấy được danh sách chương (Mục lục trống).[/bold red]")
            if interactive:
                questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()
            return

        title = info.get("book_name", f"Truyen_{book_id}") if info else f"Truyen_{book_id}"
        author = info.get("author", "Khuyết danh") if info else "Khuyết danh"
        abstract = info.get("abstract", "") if info else ""
        words = int(info.get("word_number")) if info and str(info.get("word_number", "")).strip().isdigit() else 0
        score = info.get("score", "0.0") if info else "0.0"
        
        title_safe = self.safe_filename(title)
        author_safe = self.safe_filename(author)
        
        logger.info(f"Book details: Title='{title}', Author='{author}', Chapters={len(catalog_list)}")
        
        self.console.print(Panel(
            f"[bold yellow]Truyện:[/bold yellow] [bold green]{title}[/bold green]\n"
            f"[bold yellow]Tác giả:[/bold yellow] {author}\n"
            f"[bold yellow]Điểm số:[/bold yellow] {score}★ | [bold yellow]Số từ:[/bold yellow] {words:,} từ\n"
            f"[bold yellow]Tổng số chương:[/bold yellow] {len(catalog_list)} chương\n\n"
            f"[bold yellow]Tóm tắt:[/bold yellow] {abstract[:400]}...",
            title="[bold green]XÁC NHẬN TẢI TRUYỆN[/bold green]",
            border_style="green"
        ))

        confirm = questionary.confirm("Bắt đầu tải bộ truyện này?", default=True).ask() if interactive else True
        if not confirm:
            logger.info("Download cancelled by user.")
            return

        out_dir = self.config.get("download_dir")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Temporary folder for book progress persistence
        temp_dir = os.path.join(out_dir, f".temp_{book_id}")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Scan for already completed chapters
        completed_indices = []
        pending_indices = []
        for idx in range(len(catalog_list)):
            temp_file = os.path.join(temp_dir, f"{idx}.json")
            if self.load_temp_chapter(temp_file):
                completed_indices.append(idx)
            else:
                pending_indices.append(idx)

        total_chapters = len(catalog_list)
        already_done = len(completed_indices)
        
        logger.info(f"Scan complete. Already completed: {already_done}/{total_chapters}. Pending to download: {len(pending_indices)}")
        
        if already_done > 0:
            self.console.print(f"[green]Tìm thấy tiến trình cũ: Đã tải xong {already_done}/{total_chapters} chương. Tiến hành tải tiếp...[/green]")
            time.sleep(1)

        if not pending_indices:
            logger.info("All chapters already completed. Skipping download loop, compiling output...")
            self.console.print("[green]Tất cả các chương đã tải xong! Tiến hành gộp file...[/green]")
            self.compile_output(temp_dir, out_dir, title, author, abstract, catalog_list)
            self.clean_temp_dir(temp_dir)
            self.console.print(Panel(
                f"[bold green]Tải truyện hoàn tất 100%![/bold green]\n"
                f"[bold yellow]Đường dẫn:[/bold yellow] [cyan]{os.path.abspath(self.get_final_path(out_dir, title, author))}[/cyan]",
                title="[bold green]THÀNH CÔNG[/bold green]",
                border_style="green"
            ))
            if interactive:
                questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()
            return

        concurrency = self.config.get("concurrency")
        retries = self.config.get("retry_attempts")
        
        try:
            logger.info(f"Starting ThreadPoolExecutor: Concurrency={concurrency}, Retries={retries}")
            self.console.print(f"\n[cyan]Bắt đầu tải với {concurrency} luồng đồng thời...[/cyan]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("• {task.completed}/{task.total} chương"),
                TimeRemainingColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("[green]Đang tải...", total=total_chapters)
                progress.update(task, completed=already_done)
                
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = {
                        executor.submit(
                            self.download_chapter_task, 
                            catalog_list[idx].get("item_id"), 
                            catalog_list[idx].get("catalog_title"), 
                            idx, 
                            os.path.join(temp_dir, f"{idx}.json"), 
                            retries
                        ): idx 
                        for idx in pending_indices
                    }
                    
                    for future in as_completed(futures):
                        idx = futures[future]
                        ch_info = catalog_list[idx]
                        try:
                            index, ch_title, success = future.result()
                            if success:
                                self.consecutive_failures = 0
                                progress.update(task, advance=1, description=f"[green]Đang tải: {ch_title[:25]}")
                            else:
                                self.consecutive_failures += 1
                                logger.warning(f"Failed to download chapter idx={idx} title='{ch_info.get('catalog_title')}'. Consecutive failures: {self.consecutive_failures}")
                                if self.consecutive_failures >= 15:
                                    self.restart_fanqie_app()
                                progress.update(task, description=f"[red]Lỗi: {ch_info.get('catalog_title')[:25]}")
                        except Exception as e:
                            self.consecutive_failures += 1
                            logger.error(f"Exception downloading chapter idx={idx}: {e}. Consecutive failures: {self.consecutive_failures}")
                            if self.consecutive_failures >= 15:
                                self.restart_fanqie_app()
                            progress.update(task, description=f"[red]Lỗi: {ch_info.get('catalog_title')[:25]}")

            # 4. Handle errors / retrying (Automatically go back and download error chapters)
            missing_count = self.get_missing_count(temp_dir, total_chapters)
            logger.info(f"Primary download pass completed. Missing count: {missing_count}")
            
            if missing_count > 0:
                logger.info(f"Automatically retrying {missing_count} failed chapters.")
                self.console.print(f"\n[yellow]Có {missing_count} chương tải lỗi. Tiến hành tự động tải lại các chương lỗi...[/yellow]")
                
                retry_limit = 3  # Tăng số lần thử lại tự động lên 3 lần để đạt tỷ lệ thành công cao hơn
                for attempt in range(retry_limit):
                    missing_indices = [i for i in range(total_chapters) if not os.path.exists(os.path.join(temp_dir, f"{i}.json"))]
                    if not missing_indices:
                        logger.info("All missing chapters recovered.")
                        break
                    
                    logger.info(f"Retry attempt {attempt+1}/{retry_limit}. Remaining missing: {len(missing_indices)}")
                    self.console.print(f"[yellow]Tải lại các chương lỗi (Lần {attempt+1}/{retry_limit}, còn {len(missing_indices)} chương)...[/yellow]")
                    
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(bar_width=30),
                        TextColumn("{task.completed}/{task.total} chương"),
                        console=self.console
                    ) as retry_progress:
                        retry_task = retry_progress.add_task("[yellow]Tải lại...", total=len(missing_indices))
                        
                        with ThreadPoolExecutor(max_workers=3) as retry_executor:
                            retry_futures = {
                                retry_executor.submit(
                                    self.download_chapter_task, 
                                    catalog_list[idx].get("item_id"), 
                                    catalog_list[idx].get("catalog_title"), 
                                    idx, 
                                    os.path.join(temp_dir, f"{idx}.json"), 
                                    retries + 2
                                ): idx 
                                for idx in missing_indices
                            }
                            
                            for r_future in as_completed(retry_futures):
                                try:
                                    _, _, r_success = r_future.result()
                                    if r_success:
                                        self.consecutive_failures = 0
                                        retry_progress.update(retry_task, advance=1)
                                    else:
                                        self.consecutive_failures += 1
                                        logger.warning(f"Retry failed for chapter. Consecutive failures: {self.consecutive_failures}")
                                        if self.consecutive_failures >= 15:
                                            self.restart_fanqie_app()
                                        retry_progress.update(retry_task, description="[red]Vẫn lỗi...")
                                except Exception as e:
                                    self.consecutive_failures += 1
                                    logger.error(f"Retry exception: {e}. Consecutive failures: {self.consecutive_failures}")
                                    if self.consecutive_failures >= 15:
                                        self.restart_fanqie_app()
                                    retry_progress.update(retry_task, description="[red]Vẫn lỗi...")

            # 5. Finalize output compiling
            final_missing = self.get_missing_count(temp_dir, total_chapters)
            logger.info(f"Compiling output file. Final missing count: {final_missing}")
            
            self.console.print("\n[cyan]Tiến hành gộp và lưu file truyện...[/cyan]")
            self.compile_output(temp_dir, out_dir, title, author, abstract, catalog_list)
            
            if final_missing == 0:
                logger.info("Download completed successfully at 100%. Cleaning temp dir.")
                self.clean_temp_dir(temp_dir)
                self.console.print(Panel(
                    f"[bold green]Tải truyện hoàn tất 100%![/bold green]\n"
                    f"[bold yellow]Truyện:[/bold yellow] {title}\n"
                    f"[bold yellow]Đường dẫn:[/bold yellow] [cyan]{os.path.abspath(self.get_final_path(out_dir, title, author))}[/cyan]",
                    title="[bold green]THÀNH CÔNG[/bold green]",
                    border_style="green"
                ))
            else:
                logger.warning(f"Download finished with {final_missing} missing chapters. Temp folder kept.")
                self.console.print(Panel(
                    f"[bold yellow]Đã lưu file truyện tạm thời (còn thiếu chương).[/bold yellow]\n"
                    f"[bold yellow]Đường dẫn:[/bold yellow] [cyan]{os.path.abspath(self.get_final_path(out_dir, title, author))}[/cyan]\n"
                    f"[bold red]Số chương chưa tải được:[/bold red] {final_missing}/{total_chapters} chương.\n"
                    f"[dim]Bạn có thể chạy lại lệnh tải truyện này bất kỳ lúc nào để tải tiếp các chương lỗi.[/dim]",
                    title="[bold yellow]HOÀN THÀNH MỘT PHẦN[/bold yellow]",
                    border_style="yellow"
                ))

        except KeyboardInterrupt:
            logger.warning("Download interrupted by user (KeyboardInterrupt). Saving partial progress...")
            self.console.print("\n[yellow]⚠️ Tiến trình tải bị tạm dừng bởi người dùng. Đang gộp và lưu các chương đã tải...[/yellow]")
            self.compile_output(temp_dir, out_dir, title, author, abstract, catalog_list)
            completed_cnt = self.get_completed_count(temp_dir, total_chapters)
            self.console.print(Panel(
                f"[bold yellow]Đã lưu tiến trình hiện tại vào file txt![/bold yellow]\n"
                f"[bold yellow]Đường dẫn:[/bold yellow] [cyan]{os.path.abspath(self.get_final_path(out_dir, title, author))}[/cyan]\n"
                f"[bold green]Số chương đã lưu:[/bold green] {completed_cnt}/{total_chapters} chương.\n"
                f"[dim]Chạy lại lệnh tải truyện này để tiếp tục tải các chương còn lại.[/dim]",
                title="[bold yellow]ĐÃ TẠM DỪNG[/bold yellow]",
                border_style="yellow"
            ))
            time.sleep(1)

        if interactive:
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để tiếp tục...").ask()

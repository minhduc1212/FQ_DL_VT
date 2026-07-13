# 🍅 Fanqie Novel Downloader CLI (Custom Client)

Trình tải truyện Fanqie Novel giao diện dòng lệnh (CLI) đẹp mắt, hiệu năng cao và cực kỳ ổn định. Dự án này là client tùy biến kết nối tới máy chủ API cục bộ của mô-đun **FQWeb (Xposed Module)** chạy trên điện thoại hoặc giả lập Android.

---

## 🌟 Tính Năng Nổi Bật (Core Features)

1. **Tải truyện đa dạng:** Hỗ trợ tìm kiếm theo tên truyện, tên tác giả, khám phá theo thể loại hoặc tải trực tiếp bằng ID truyện / URL link chia sẻ của Fanqie Novel.
2. **Lưu tiến trình tức thì (Save as you go):** Tải đến đâu lưu file tạm JSON của từng chương đến đó ngay lập tức để tiết kiệm bộ nhớ RAM và bảo vệ dữ liệu khi tiến trình bị ngắt đột ngột.
3. **Tiếp tục tải thông minh (Resume):** Tự động quét thư mục tạm, nhận diện các chương đã tải thành công để bỏ qua và chỉ tải các chương còn thiếu khi bạn chạy lại lệnh tải.
4. **Tải tuần tự & Đa luồng (Sequential & Multi-threaded):** Hỗ trợ tùy chỉnh số lượng luồng tải đồng thời (từ 1 đến 20 luồng). Chế độ 1 luồng (tải tuần tự) giúp tối đa hóa sự ổn định cho các máy cấu hình thấp.
5. **Cấu hình độ trễ (Request Delay):** Tự động điều chỉnh khoảng nghỉ giữa các chương và kích hoạt cơ chế khởi động lệch mili-giây (staggering) cho đa luồng để bảo vệ ứng dụng Fanqie khỏi bị treo cache hoặc chặn API (RPC Exception).
6. **Tự động khởi động lại App qua ADB (Auto-Recovery):** Khi phát hiện 15 lỗi liên tiếp (app Fanqie bị đơ/nghẽn RAM), chương trình sẽ tự động kích hoạt ADB tắt app, bật lại app, thiết lập ADB Port Forward và thăm dò trạng thái kết nối chủ động (Active Connection Polling) cho tới khi server FQWeb online rồi mới tiếp tục tải.
7. **Nhật ký hoạt động chuyên nghiệp (Logging):** Toàn bộ hoạt động, lỗi kết nối, thông số tải đều được ghi nhận chi tiết vào file log xoay vòng `logs/downloader.log` (tự động chia file khi đạt 5MB). Bạn có thể xem trực tiếp 30 dòng log gần nhất ngay trên menu ứng dụng.

---

## ⚙️ Yêu Cầu Hệ Thống (Prerequisites)

* **Thiết bị Android / Giả lập (Khuyến nghị LDPlayer):**
  * Đã cài đặt ứng dụng **番茄小说 (Fanqie Novel)** (Phiên bản khuyến nghị: `5.7.9.32` hoặc `5.8.3.32`).
  * Đã cài đặt môi trường Xposed (LSPosed) và kích hoạt mô-đun **FQWeb**.
  * Đã bật chức năng **Web API** trong phần cài đặt của app Fanqie.
* **Máy tính chạy tool:**
  * Đã cài đặt **Python 3.8 trở lên**.
  * Đã cài đặt công cụ **ADB (Android Debug Bridge)** và thêm vào biến môi trường hệ thống (`PATH`).

---

## 🚀 Hướng Dẫn Cài Đặt (Installation)

1. Tải toàn bộ mã nguồn dự án về máy tính của bạn.
2. Mở Terminal / PowerShell tại thư mục dự án và khởi tạo môi trường ảo Python (khuyến nghị):
   ```bash
   python -m venv .venv
   ```
3. Kích hoạt môi trường ảo:
   * Trên Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   * Trên macOS / Linux:
     ```bash
     source .venv/bin/activate
     ```
4. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📖 Hướng Dẫn Sử Dụng (How to Use)

1. Khởi động điện thoại hoặc giả lập Android (đảm bảo dịch vụ ADB đã nhận diện thiết bị bằng lệnh `adb devices`).
2. Mở ứng dụng **Fanqie Novel** trên giả lập.
3. Chạy chương trình chính trên máy tính:
   ```bash
   python main.py
   ```
4. Hệ thống sẽ tự động kiểm tra cổng kết nối `9999` (nếu cổng offline, nó sẽ tự động chạy lệnh `adb forward tcp:9999 tcp:9999`).
5. Giao diện menu điều khiển tương tác trực quan bằng phím mũi tên và nút bấm sẽ xuất hiện:
   * **🔍 Tìm kiếm truyện theo Tên:** Nhập từ khóa tìm kiếm sách.
   * **👤 Tìm kiếm truyện theo Tác giả:** Tìm kiếm sách của một tác giả cụ thể.
   * **🧭 Khám phá truyện theo Thể loại:** Duyệt qua danh sách 15 thể loại sách phổ biến.
   * **🆔 Tải truyện bằng ID:** Dán ID truyện (Ví dụ: `7484611801053678654`).
   * **🔗 Tải truyện bằng URL/Link:** Dán link chia sẻ trang chi tiết truyện.
   * **📋 Xem Nhật Ký Hoạt Động:** Xem trực tiếp log ghi nhận hoạt động gần nhất.
   * **⚙️ Cấu hình cài đặt:** Chỉnh sửa số luồng, độ trễ, thư mục tải, định dạng lưu file.
   * **❌ Thoát chương trình:** Đóng ứng dụng an toàn.

---

## 🛠️ Cài Đặt Tham Số Khuyên Dùng (Recommended Settings)

Để tiến trình tải mượt mà không bị gián đoạn hay phát sinh lỗi RPC của server ByteDance:
* **Tải tốc độ cao (Đa luồng):** Số luồng: `5` -> `8` luồng | Độ trễ (Delay): `0.3` -> `0.5` giây.
* **Tải siêu ổn định (Không lỗi):** Số luồng: `1` luồng (Tải lần lượt) | Độ trễ (Delay): `0.3` -> `0.5` giây.

---

## 📂 Cấu Trúc Mã Nguồn (Project Structure)

```text
├── src/
│   ├── api.py           # Gọi các HTTP Endpoint của FQWeb API & ADB forward
│   ├── config.py        # Quản lý cấu hình lưu trữ qua file JSON
│   ├── downloader.py    # Điều phối tải đa luồng, lưu file tạm, tự động phục hồi lỗi
│   ├── logger.py        # Cấu hình log xoay vòng (Rotating log file)
│   └── ui.py            # Vẽ giao diện CLI Console tương tác (Rich, Questionary)
├── logs/
│   └── downloader.log   # File nhật ký hoạt động chi tiết (Được tự tạo khi chạy)
├── config.json          # File lưu trữ thông số cài đặt (Được tự tạo khi chạy)
├── main.py              # Điểm khởi chạy chương trình (Entrypoint)
├── requirements.txt     # Danh sách thư viện Python phụ thuộc
└── README.md            # Tài liệu hướng dẫn sử dụng
```

---

## 🛑 Cách Dừng Tiến Trình Tải (Stop & Pause)

* Khi chương trình đang tải truyện, bạn có thể nhấn tổ hợp phím **`Ctrl + C`** để dừng tải bất kỳ lúc nào.
* Phần mềm sẽ bắt ngoại lệ và **tự động gộp toàn bộ các chương đã tải xong trước đó** vào file kết quả `.txt` để bạn đọc được ngay phần đã tải, đồng thời bảo tồn file tạm để lần sau tiếp tục tải các phần còn lại.

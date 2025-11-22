# Hướng dẫn cài đặt và chạy ứng dụng

Làm theo các bước sau để khởi chạy hệ thống (Server Backend + GUI Frontend).

## 1. Cài đặt thư viện

### Bước 1: Cài đặt cho GUI
Từ thư mục gốc, đi vào thư mục `gui` và cài đặt các thư viện cần thiết:

```bash
cd gui
pip install -r requirements.txt
```

### Bước 2: Cài đặt cho Server (Python API)
Quay lại thư mục gốc hoặc đi sang thư mục `python` và cài đặt thư viện:

```bash
cd ../python
pip install -r requirements.txt
```

## 2. Chạy ứng dụng

### Bước 1: Khởi động Server
Trong thư mục `python`, chạy script `run.sh` để bật API Server:

```bash
# Đang ở trong thư mục python
./run.sh
```
*Lưu ý: Server sẽ chạy tại địa chỉ mặc định (thường là `http://localhost:8000`). Giữ cửa sổ terminal này mở.*

### Bước 2: Khởi động GUI App
Mở một terminal mới, đi vào thư mục `gui` và chạy file `app.py`:

```bash
# Từ thư mục gốc
cd gui
python app.py
```

Lúc này giao diện ứng dụng sẽ hiện lên và tự động kết nối với Server.
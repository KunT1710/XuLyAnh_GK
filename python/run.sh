#!/bin/bash

# Dừng script nếu có lỗi
set -e

# echo "Cài đặt package..."
# pip install -r requirements.txt

echo "Khởi động server FastAPI..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

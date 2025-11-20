import uuid
import cv2
import os

TEMP_DIR = "temp"

# Tạo thư mục temp nếu chưa có
os.makedirs(TEMP_DIR, exist_ok=True)

def save_temp_image(image):
    """
    Lưu ảnh thành file PNG tạm trong thư mục ./temp
    """
    file_path = os.path.join(TEMP_DIR, f"temp_{uuid.uuid4().hex}.png")
    cv2.imwrite(file_path, image)
    return file_path

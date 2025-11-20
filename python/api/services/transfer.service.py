import cv2
import numpy as np

# [POST] /transfer/gray
def to_gray(img: np.ndarray) -> np.ndarray:
    """
    Chuyển ảnh sang grayscale.
    """
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# [POST] /transfer/binary
def to_binary(img: np.ndarray, thresh: int = 127) -> np.ndarray:
    """
    Chuyển ảnh sang nhị phân (binary) theo threshold.
    - thresh: 0..255
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    return binary

# [POST] /transfer/brightness
def adjust_brightness(img: np.ndarray, beta: int = 0) -> np.ndarray:
    """
    Điều chỉnh độ sáng ảnh.
    - beta: -100..100 (âm giảm sáng, dương tăng sáng)
    """
    beta = np.clip(beta, -100, 100)
    bright = cv2.convertScaleAbs(img, alpha=1.0, beta=beta)
    return bright

# [POST] /transfer/blur
def apply_blur(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """
    Làm mờ ảnh (Gaussian Blur).
    - ksize: số lẻ > 1
    """
    if ksize % 2 == 0:
        ksize += 1 
    ksize = max(3, ksize) 
    blurred = cv2.GaussianBlur(img, (ksize, ksize), 0)
    return blurred


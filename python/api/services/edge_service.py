import cv2
import numpy as np

# [POST] /edge-detect/sobel
def sobel_edge(img: np.ndarray) -> np.ndarray:
    """
    Áp dụng Sobel Edge Detection.
    - Chuyển ảnh về xám
    - Tính gradient theo X và Y
    - Kết hợp magnitude
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)

    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    magnitude = cv2.magnitude(grad_x, grad_y)

    magnitude = np.uint8(np.clip(magnitude, 0, 255))
    
    return magnitude

# [POST] /edge-detect/prewitt
def prewitt_edge(img: np.ndarray) -> np.ndarray:
    """
    Áp dụng Prewitt Edge Detection.
    - Kernel Prewitt chuẩn
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    kernel_x = np.array([[ -1, 0, 1],
                         [ -1, 0, 1],
                         [ -1, 0, 1]], dtype=np.float32)
    kernel_y = np.array([[ 1, 1, 1],
                         [ 0, 0, 0],
                         [-1,-1,-1]], dtype=np.float32)
    
    grad_x = cv2.filter2D(gray, cv2.CV_64F, kernel_x)
    grad_y = cv2.filter2D(gray, cv2.CV_64F, kernel_y)
    
    magnitude = cv2.magnitude(grad_x, grad_y)
    magnitude = np.uint8(np.clip(magnitude, 0, 255))
    
    return magnitude

# [POST] /edge-detect/robert
def robert_edge(img: np.ndarray) -> np.ndarray:
    """
    Áp dụng Robert Cross Edge Detection.
    - Kernel Robert chuẩn
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    kernel_x = np.array([[1, 0],
                         [0,-1]], dtype=np.float32)
    kernel_y = np.array([[0, 1],
                         [-1,0]], dtype=np.float32)
    
    grad_x = cv2.filter2D(gray, cv2.CV_64F, kernel_x)
    grad_y = cv2.filter2D(gray, cv2.CV_64F, kernel_y)
    
    magnitude = cv2.magnitude(grad_x, grad_y)
    magnitude = np.uint8(np.clip(magnitude, 0, 255))
    
    return magnitude

# [POST] /edge-detect/canny
def canny_edge(img: np.ndarray, low_threshold: int = 50, high_threshold: int = 150) -> np.ndarray:
    """
    Áp dụng Canny Edge Detection.
    - low_threshold: ngưỡng dưới
    - high_threshold: ngưỡng trên
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5,5), 1.4)
    
    edges = cv2.Canny(blurred, threshold1=low_threshold, threshold2=high_threshold)
    return edges

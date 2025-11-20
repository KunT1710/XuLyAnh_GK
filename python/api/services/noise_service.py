import numpy as np
import cv2

# [POST] /noise/salt-pepper
def add_salt_pepper_noise(img, amount=0.02):
    """
    Thêm nhiễu muối tiêu.
    amount: tỷ lệ pixel bị nhiễu (0..1)
    """
    row, col, ch = img.shape
    out = img.copy()
    num_salt = np.ceil(amount * img.size * 0.5)
    num_pepper = np.ceil(amount * img.size * 0.5)

    coords = [np.random.randint(0, i-1, int(num_salt)) for i in img.shape[:2]]
    out[coords[0], coords[1], :] = 255

    coords = [np.random.randint(0, i-1, int(num_pepper)) for i in img.shape[:2]]
    out[coords[0], coords[1], :] = 0

    return out
  
# [POST] /noise/gaussian
def add_gaussian_noise(img, mean=0.0, sigma=10.0):
    """
    Thêm nhiễu Gaussian.
    mean: trung bình
    sigma: độ lệch chuẩn
    """
    gauss = np.random.normal(mean, sigma, img.shape).astype(np.float32)
    noisy = img.astype(np.float32) + gauss
    noisy = np.clip(noisy, 0, 255).astype(np.uint8)
    return noisy

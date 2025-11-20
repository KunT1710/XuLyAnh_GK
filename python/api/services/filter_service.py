import cv2

# [POST] /filter/mean
def mean_filter(img, ksize=3):
    if ksize % 2 == 0:
        ksize += 1
    return cv2.blur(img, (ksize, ksize))

# [POST] /filter/meadian
def median_filter(img, ksize=3):
    if ksize % 2 == 0:
        ksize += 1
    return cv2.medianBlur(img, ksize)

# [POST] /filter/gaussian
def gaussian_filter(img, ksize=3, sigma=0):
    if ksize % 2 == 0:
        ksize += 1
    return cv2.GaussianBlur(img, (ksize, ksize), sigma)
import cv2
import numpy as np

# [POST] /cut/bg-with-rect
def remove_background_with_rect(img, rect, iterations=5):
    """Xử lý tách nền bằng GrabCut với Rect."""
    
    mask = np.zeros(img.shape[:2], np.uint8)
    bgModel = np.zeros((1, 65), np.float64)
    fgModel = np.zeros((1, 65), np.float64)

    cv2.grabCut(img, mask, rect, bgModel, fgModel, iterations, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 1) | (mask == 3), 1, 0).astype("uint8")

    result = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    result[:, :, 3] = mask2 * 255

    return result


def remove_background_auto(img):
    mask = np.zeros(img.shape[:2], np.uint8)

    # Initialize GrabCut rectangle to cover gần hết ảnh
    height, width = img.shape[:2]
    rect = (10, 10, width-20, height-20)

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)

    mask2 = np.where((mask==2)|(mask==0), 0, 1).astype('uint8')
    result = img * mask2[:, :, np.newaxis]

    # convert BG trong suốt
    b, g, r = cv2.split(result)
    alpha = mask2*255
    result = cv2.merge([b, g, r, alpha])

    return result
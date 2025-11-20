from fastapi import APIRouter, Form
import numpy as np
import cv2
import os

from api.services.filter_service import mean_filter, median_filter, gaussian_filter
from api.utils.session import load_current_image, save_current_image, load_history, save_history

router = APIRouter(prefix="/filter", tags=["Image Filters"])

@router.post("/mean")
async def mean_filter_api(
    session_id: str = Form(...),
    ksize: int = Form(3)
):
    """
    Áp dụng lọc trung bình (Mean Filter) lên ảnh hiện tại trong session.
    """
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    # 1. Load current image
    img = load_current_image(session_path)
    if img is None:
        return {"error": "Không tìm thấy current image"}

    # 2. Fix kernel size
    if ksize % 2 == 0:
        ksize += 1
    ksize = max(3, ksize)

    # 3. Áp dụng filter
    result = mean_filter(img, ksize)

    # 4. Load history + trim redo
    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"]+1]

    # 5. Lưu step mới
    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    file_path = f"{session_path}/history/{file_name}"
    cv2.imwrite(file_path, result)

    history["steps"].append({"file": file_name, "action": "mean_filter"})
    history["current_step"] = step_id
    save_history(session_path, history)

    # 6. Ghi đè current.png
    save_current_image(session_path, result)

    return {"message": "success", "step": step_id}


@router.post("/median")
async def median_filter_api(
    session_id: str = Form(...),
    ksize: int = Form(3)
):
    """
    Áp dụng lọc trung vị (Median Filter) lên ảnh hiện tại trong session.
    """
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    img = load_current_image(session_path)
    if img is None:
        return {"error": "Không tìm thấy current image"}

    if ksize % 2 == 0:
        ksize += 1
    ksize = max(3, ksize)

    result = median_filter(img, ksize)

    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"]+1]

    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    file_path = f"{session_path}/history/{file_name}"
    cv2.imwrite(file_path, result)

    history["steps"].append({"file": file_name, "action": "median_filter"})
    history["current_step"] = step_id
    save_history(session_path, history)

    save_current_image(session_path, result)

    return {"message": "success", "step": step_id}


@router.post("/gaussian")
async def gaussian_filter_api(
    session_id: str = Form(...),
    ksize: int = Form(3),
    sigma: float = Form(0)
):
    """
    Áp dụng lọc Gaussian lên ảnh hiện tại trong session.
    """
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    img = load_current_image(session_path)
    if img is None:
        return {"error": "Không tìm thấy current image"}

    if ksize % 2 == 0:
        ksize += 1
    ksize = max(3, ksize)

    result = gaussian_filter(img, ksize, sigma)

    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"]+1]

    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    file_path = f"{session_path}/history/{file_name}"
    cv2.imwrite(file_path, result)

    history["steps"].append({"file": file_name, "action": "gaussian_filter"})
    history["current_step"] = step_id
    save_history(session_path, history)

    save_current_image(session_path, result)

    return {"message": "success", "step": step_id}

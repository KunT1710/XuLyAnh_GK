from fastapi import APIRouter, Form
import numpy as np
import cv2
import os
from api.services.noise_service import add_salt_pepper_noise, add_gaussian_noise
from api.utils.session import load_current_image, save_current_image, load_history, save_history

router = APIRouter(prefix="/noise", tags=["Add Noise"])

@router.post("/salt-pepper")
async def salt_pepper_api(
    session_id: str = Form(...),
    amount: float = Form(0.02)
):
    """
    Thêm nhiễu muối tiêu vào ảnh hiện tại trong session
    """
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    # 1. Load current image
    img = load_current_image(session_path)
    if img is None:
        return {"error": "Không tìm thấy current image"}

    # 2. Thêm nhiễu
    amount = np.clip(amount, 0, 1)
    result = add_salt_pepper_noise(img, amount)

    # 3. Load history
    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"]+1]

    # 4. Lưu step mới
    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    file_path = f"{session_path}/history/{file_name}"
    cv2.imwrite(file_path, result)

    history["steps"].append({"file": file_name, "action": "salt_pepper"})
    history["current_step"] = step_id
    save_history(session_path, history)

    # 5. Ghi đè current.png
    save_current_image(session_path, result)

    return {"message": "success", "step": step_id}


@router.post("/gaussian")
async def gaussian_api(
    session_id: str = Form(...),
    mean: float = Form(0.0),
    sigma: float = Form(10.0)
):
    """
    Thêm nhiễu Gaussian vào ảnh hiện tại trong session
    """
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    # 1. Load current image
    img = load_current_image(session_path)
    if img is None:
        return {"error": "Không tìm thấy current image"}

    # 2. Thêm nhiễu Gaussian
    result = add_gaussian_noise(img, mean, sigma)

    # 3. Load history + trim redo
    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"]+1]

    # 4. Lưu step mới
    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    file_path = f"{session_path}/history/{file_name}"
    cv2.imwrite(file_path, result)

    history["steps"].append({"file": file_name, "action": "gaussian"})
    history["current_step"] = step_id
    save_history(session_path, history)

    # 5. Ghi đè current.png
    save_current_image(session_path, result)

    return {"message": "success", "step": step_id}

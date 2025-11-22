from fastapi import APIRouter, Form, UploadFile,File
from api.utils.session import load_current_image, save_current_image, load_history, save_history
from api.services.transfer_service import to_gray, to_binary, adjust_brightness, apply_blur
import cv2
import os

router = APIRouter(prefix="/transfer", tags=["Color & Image Adjustment"])


@router.post("/gray")
async def gray_api(session_id: str = Form(...)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    img = load_current_image(session_path)
    if img is None:
        return {"error": "Không tìm thấy ảnh current trong session"}

    # --- Gọi service xử lý ---
    result = to_gray(img)

    # --- Cập nhật history ---
    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"] + 1]
    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    cv2.imwrite(f"{session_path}/history/{file_name}", result)
    history["steps"].append({"file": file_name, "action": "gray"})
    history["current_step"] = step_id
    save_history(session_path, history)

    save_current_image(session_path, result)
    return {"message": "success", "step": step_id}


@router.post("/binary")
async def binary_api(session_id: str = Form(...), thresh: int = Form(127)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    img = load_current_image(session_path)
    if img is None:
        return {"error": "No current image"}

    result = to_binary(img, thresh)

    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"] + 1]
    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    cv2.imwrite(f"{session_path}/history/{file_name}", result)
    history["steps"].append({"file": file_name, "action": "binary"})
    history["current_step"] = step_id
    save_history(session_path, history)

    save_current_image(session_path, result)
    return {"message": "success", "step": step_id}


@router.post("/brightness")
async def brightness_api(session_id: str = Form(...), beta: int = Form(0)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    img = load_current_image(session_path)
    if img is None:
        return {"error": "No current image"}

    result = adjust_brightness(img, beta)

    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"] + 1]
    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    cv2.imwrite(f"{session_path}/history/{file_name}", result)
    history["steps"].append({"file": file_name, "action": "brightness"})
    history["current_step"] = step_id
    save_history(session_path, history)

    save_current_image(session_path, result)
    return {"message": "success", "step": step_id}


@router.post("/blur")
async def blur_api(session_id: str = Form(...), ksize: int = Form(5)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    img = load_current_image(session_path)
    if img is None:
        return {"error": "No current image"}

    result = apply_blur(img, ksize)

    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"] + 1]
    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    cv2.imwrite(f"{session_path}/history/{file_name}", result)
    history["steps"].append({"file": file_name, "action": "blur"})
    history["current_step"] = step_id
    save_history(session_path, history)

    save_current_image(session_path, result)
    return {"message": "success", "step": step_id}



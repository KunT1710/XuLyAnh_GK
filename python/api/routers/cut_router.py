from fastapi import APIRouter, Form
import cv2
import os
from api.services.cut_service import remove_background_with_rect, remove_background_auto
from api.utils.session import load_current_image, save_current_image, load_history, save_history

router = APIRouter(prefix="/cut", tags=["Background Removal"])

def apply_bg_removal(session_path: str, func, action_name: str, rect=None):
    # 1. Load current image
    img = load_current_image(session_path)
    if img is None:
        return {"error": "Không tìm thấy current image"}

    # 2. Xử lý tách nền
    if rect:
        result = func(img, rect)
    else:
        result = func(img)

    # 3. Load history + trim redo chain
    history = load_history(session_path)
    history["steps"] = history["steps"][:history["current_step"] + 1]

    # 4. Lưu step mới
    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"
    file_path = f"{session_path}/history/{file_name}"
    cv2.imwrite(file_path, result)

    history["steps"].append({"file": file_name, "action": action_name})
    history["current_step"] = step_id
    save_history(session_path, history)

    # 5. Ghi đè current.png
    save_current_image(session_path, result)

    return {"message": "success", "step": step_id}


@router.post("/bg-with-rect")
async def remove_bg_rect_api(
    session_id: str = Form(...),
    x: int = Form(...),
    y: int = Form(...),
    w: int = Form(...),
    h: int = Form(...)
):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    rect = (x, y, w, h)
    return apply_bg_removal(session_path, remove_background_with_rect, "bg_with_rect", rect=rect)


@router.post("/bg-auto")
async def remove_bg_auto_api(session_id: str = Form(...)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    return apply_bg_removal(session_path, remove_background_auto, "bg_auto")

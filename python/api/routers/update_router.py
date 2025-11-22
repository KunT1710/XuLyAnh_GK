
from fastapi import APIRouter, Form, UploadFile,File
from api.utils.session import load_current_image, save_current_image, load_history, save_history
from api.services.transfer_service import to_gray, to_binary, adjust_brightness, apply_blur
import cv2
import os
import numpy as np

router = APIRouter(tags=["Color & Image Adjustment"])

@router.post("/update")
async def update_api(session_id: str = Form(...), file: UploadFile = File(...)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    # ĐỌC FILE ẢNH UPLOAD
    data = await file.read()
    nparr = np.frombuffer(data, np.uint8)
    new_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if new_img is None:
        return {"error": "Invalid image"}

    # LOAD CURRENT IMAGE (để đưa vào history)
    current_img = load_current_image(session_path)
    if current_img is None:
        return {"error": "No current image to replace"}

    # LOAD HISTORY
    history = load_history(session_path)

    # CẮT CÁC BƯỚC REDO (nếu user đã undo rồi update)
    history["steps"] = history["steps"][:history["current_step"] + 1]

    # TẠO BƯỚC MỚI
    step_id = history["current_step"] + 1
    file_name = f"step_{step_id}.png"

    # LƯU new_img VÀO HISTORY (Fix: Lưu ảnh mới thay vì ảnh cũ)
    cv2.imwrite(f"{session_path}/history/{file_name}", new_img)

    history["steps"].append({
        "file": file_name,
        "action": "update"
    })
    history["current_step"] = step_id

    save_history(session_path, history)

    save_current_image(session_path, new_img)

    return {"message": "updated successfully", "step": step_id}

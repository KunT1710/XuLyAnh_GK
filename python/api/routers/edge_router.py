from fastapi import APIRouter, Form
import cv2
import os
from api.services.edge_service import sobel_edge, prewitt_edge, robert_edge, canny_edge
from api.utils.session import load_current_image, save_current_image, load_history, save_history

router = APIRouter(prefix="/edge-detect", tags=["Edge Detection"])

def apply_edge(session_path: str, edge_func, action_name: str):
    # 1. Load current image
    img = load_current_image(session_path)
    if img is None:
        return {"error": "Không tìm thấy current image"}

    # 2. Áp dụng edge detection
    result = edge_func(img)

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


@router.post("/sobel")
async def sobel_api(session_id: str = Form(...)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)
    return apply_edge(session_path, sobel_edge, "sobel_edge")


@router.post("/prewitt")
async def prewitt_api(session_id: str = Form(...)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)
    return apply_edge(session_path, prewitt_edge, "prewitt_edge")


@router.post("/robert")
async def robert_api(session_id: str = Form(...)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)
    return apply_edge(session_path, robert_edge, "robert_edge")


@router.post("/canny")
async def canny_api(session_id: str = Form(...)):
    session_path = f"sessions/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)
    return apply_edge(session_path, canny_edge, "canny_edge")

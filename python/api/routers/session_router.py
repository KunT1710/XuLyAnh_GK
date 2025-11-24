from fastapi import APIRouter, UploadFile, File,HTTPException
import uuid, os, json, cv2
import numpy as np
import shutil
from api.utils.auth import create_token

router = APIRouter(prefix="/session", tags=["Session"])

BASE_DIR = "sessions"

@router.post("/create")
async def create_session(file: UploadFile = File(...)):
    # 1. Tạo session_id
    session_id = str(uuid.uuid4())
    session_path = f"{BASE_DIR}/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    img_bytes = await file.read()
    img_np = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    if img is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid image file")

    original_path = f"{session_path}/original.png"
    current_path = f"{session_path}/current.png"

    cv2.imwrite(original_path, img)
    cv2.imwrite(current_path, img)

    history = {
        "current_step": 0,
        "steps": [
            {"file": "step_0.png", "action": "original"}
        ]
    }

    cv2.imwrite(f"{session_path}/history/step_0.png", img)

    with open(f"{session_path}/history.json", "w") as f:
        json.dump(history, f)
    token_data = {"sub": session_id} 
    session_token = create_token(data=token_data)
    return {
        "session_id": session_id,
        "access_token": session_token,
        "token_type": "bearer"
    }


@router.delete("/delete/{session_id}")
async def delete_session(session_id: str):

    if not session_id.replace("-", "").isalnum():
         raise HTTPException(status_code=400, detail="Invalid session ID format")

    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session_path = os.path.join(BASE_DIR, session_id)

    if not os.path.abspath(session_path).startswith(os.path.abspath(BASE_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(session_path):
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' không tồn tại!"
        )

    try:
        shutil.rmtree(session_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Không thể xoá session: {str(e)}"
        )

    return {
        "status": "success",
        "message": f"Session '{session_id}' đã được xoá thành công."
    }
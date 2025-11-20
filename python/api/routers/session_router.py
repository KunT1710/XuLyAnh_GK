from fastapi import APIRouter, UploadFile, File
import uuid, os, json, cv2
import numpy as np

router = APIRouter(prefix="/session", tags=["Session"])

BASE_DIR = "sessions"

@router.post("/create")
async def create_session(file: UploadFile = File(...)):
    # 1. Tạo session_id
    session_id = str(uuid.uuid4())
    session_path = f"{BASE_DIR}/{session_id}"
    os.makedirs(f"{session_path}/history", exist_ok=True)

    # 2. Lưu ảnh gốc
    img_bytes = await file.read()
    img_np = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

    original_path = f"{session_path}/original.png"
    current_path = f"{session_path}/current.png"

    cv2.imwrite(original_path, img)
    cv2.imwrite(current_path, img)

    # 3. Khởi tạo history.json
    history = {
        "current_step": 0,
        "steps": [
            {"file": "step_0.png", "action": "original"}
        ]
    }

    cv2.imwrite(f"{session_path}/history/step_0.png", img)

    with open(f"{session_path}/history.json", "w") as f:
        json.dump(history, f)

    return {"session_id": session_id}

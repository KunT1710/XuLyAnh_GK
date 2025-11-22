import os
import json
import cv2
import shutil

def _save_history_json(session_path, history):
    with open(f"{session_path}/history.json", "w") as f:
        json.dump(history, f, indent=4)

def _load_history_json(session_path):
    history_path = f"{session_path}/history.json"
    if not os.path.exists(history_path):
        return None
    with open(history_path, "r") as f:
        return json.load(f)

def get_current_image_url(session_id: str):
    return f"/undo_redo/current?session_id={session_id}"

def apply_undo(session_path: str):
    history = _load_history_json(session_path)
    if history is None:
        return {"error": "Không tìm thấy history.json",
                "session_path": session_path}

    current_step = history["current_step"]
    if current_step <= 0:
        return {"error": "Không thể undo nữa"}

    new_step = current_step - 1
    img_file = f"{session_path}/history/step_{new_step}.png"
    if not os.path.exists(img_file):
        return {"error": "Không tìm thấy file history để undo"}

    img = cv2.imread(img_file)
    if img is None:
        return {"error": "Không load được ảnh history"}

    cv2.imwrite(f"{session_path}/current.png", img)
    history["current_step"] = new_step
    _save_history_json(session_path, history)

    return {
        "message": "undo_success",
        "step": new_step,
        "action": history["steps"][new_step]["action"],
        "current_image": get_current_image_url(os.path.basename(session_path))
    }

def apply_redo(session_path: str):
    history = _load_history_json(session_path)
    if history is None:
        return {"error": "Không tìm thấy history.json",
                "session_path": session_path}

    current_step = history["current_step"]
    steps = history["steps"]

    if current_step >= len(steps) - 1:
        return {"error": "Không thể redo nữa"}

    new_step = current_step + 1
    img_file = f"{session_path}/history/step_{new_step}.png"
    if not os.path.exists(img_file):
        return {"error": "Không tìm thấy file history để redo"}

    img = cv2.imread(img_file)
    if img is None:
        return {"error": "Không load được ảnh history"}

    cv2.imwrite(f"{session_path}/current.png", img)
    history["current_step"] = new_step
    _save_history_json(session_path, history)

    return {
        "message": "redo_success",
        "step": new_step,
        "action": history["steps"][new_step]["action"],
        "current_image": get_current_image_url(os.path.basename(session_path))
    }

def reset_history(session_path: str):
    history_folder = f"{session_path}/history"
    original = f"{session_path}/original.png"
    current = f"{session_path}/current.png"

    if not os.path.exists(original):
        return {"error": "Không tìm thấy ảnh original để reset"}

    if os.path.exists(history_folder):
        shutil.rmtree(history_folder)
    os.makedirs(history_folder, exist_ok=True)

    shutil.copy(original, current)

    history = {
        "current_step": 0,
        "steps": [
            {"file": "step_0.png", "action": "original"}
        ]
    }

    cv2.imwrite(f"{history_folder}/step_0.png", cv2.imread(original))
    _save_history_json(session_path, history)

    return {
        "message": "reset_success",
        "step": 0,
        "action": "original",
        "current_image": get_current_image_url(os.path.basename(session_path))
    }

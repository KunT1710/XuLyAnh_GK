import json, cv2

def load_current_image(session_path):
    return cv2.imread(f"{session_path}/current.png")

def save_current_image(session_path, img):
    cv2.imwrite(f"{session_path}/current.png", img)

def load_history(session_path):
    with open(f"{session_path}/history.json") as f:
        return json.load(f)

def save_history(session_path, history):
    with open(f"{session_path}/history.json", "w") as f:
        json.dump(history, f, indent=4)

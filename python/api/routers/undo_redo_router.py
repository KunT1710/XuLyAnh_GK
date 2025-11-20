from fastapi import APIRouter, Form
from fastapi.responses import FileResponse
import os
from api.utils.undo_redo import apply_undo, apply_redo, reset_history

router = APIRouter(prefix="/undo_redo", tags=["Color & Image Adjustment"])

@router.post("/undo")
async def undo_api(session_id: str = Form(...)):
    session_path = os.path.join("sessions", session_id)
    if not os.path.exists(session_path):
        return {"error": "Invalid session_id"}
    return apply_undo(session_path)

@router.post("/redo")
async def redo_api(session_id: str = Form(...)):
    session_path = os.path.join("sessions", session_id)
    if not os.path.exists(session_path):
        return {"error": "Invalid session_id"}
    return apply_redo(session_path)

@router.post("/reset")
async def reset_api(session_id: str = Form(...)):
    session_path = os.path.join("sessions", session_id)
    if not os.path.exists(session_path):
        return {"error": "Invalid session_id"}
    return reset_history(session_path)

@router.get("/current")
async def get_current(session_id: str):
    path = os.path.join("sessions", session_id, "current.png")
    if not os.path.exists(path):
        return {"error": "No current image for this session"}
    return FileResponse(path, media_type="image/png")

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from api.routers import cut_router, noise_router, edge_router, transfer_router, session_router, undo_redo_router, filter_router, update_router
from api.utils.auth import verify_token
import os, logging
# middleware
class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/", "/docs", "/openapi.json", "/session/create"]:
            return await call_next(request)

        token = request.headers.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Missing token")

        try:
            verify_token(token)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")

        return await call_next(request)
    
# fastAPI
app = FastAPI(
    title="Image Processing API",
    description="API xử lý ảnh cho đồ án XLA",
    version="1.0.0",
)

# Logging 
logging.basicConfig(level=logging.INFO)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# add middleware
app.add_middleware(JWTMiddleware)

# router
app.include_router(cut_router.router)
app.include_router(noise_router.router)
app.include_router(edge_router.router)
app.include_router(transfer_router.router)
app.include_router(session_router.router)
app.include_router(undo_redo_router.router)
app.include_router(filter_router.router)
app.include_router(update_router.router)

#  Ensure session folder exists
if not os.path.exists("sessions"):
    os.makedirs("sessions", exist_ok=True)

# root
@app.get("/")
def home():
    """
    Kiểm tra API có đang chạy không.
    """
    return {
        "code": 200,
        "message": "Image Processing API is running!"
    }


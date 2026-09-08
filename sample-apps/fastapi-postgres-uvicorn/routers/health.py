from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health():
    return JSONResponse({"status": "ok"})


@router.get("/ping")
async def ping():
    return JSONResponse({"ping": "pong"})

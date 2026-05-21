from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

from app.database import init_db, engine

app = FastAPI(
    title="BookGuard 珍贵图书数字化保护系统",
    description="基于 UmiOCR 的手写文字识别与珍贵图书数字化保护平台",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


from app.routers import books, ocr, export, recyclebin, auth
app.include_router(books.router)
app.include_router(ocr.router)
app.include_router(export.router)
app.include_router(recyclebin.router)
app.include_router(auth.router)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        file_path = os.path.join(STATIC_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)

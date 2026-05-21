from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os

from app.database import init_db

app = FastAPI(
    title="BookGuard",
    description="BookGuard",
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
        if path.startswith("api/") or path.startswith("docs") or path.startswith("openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        file_path = os.path.join(STATIC_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port)

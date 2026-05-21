import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database import get_db
from app.services import export_service
from app.schemas import ExportRequest, ExportResponse

router = APIRouter(prefix="/api/export", tags=["导出管理"])


@router.post("", summary="导出图书")
async def export_book(data: ExportRequest, db: AsyncSession = Depends(get_db)):
    try:
        if data.export_format == "txt":
            filepath = await export_service.export_book_txt(db, data.book_id, data.page_range)
        elif data.export_format == "json":
            filepath = await export_service.export_book_json(db, data.book_id, data.page_range)
        elif data.export_format == "md":
            filepath = await export_service.export_book_md(db, data.book_id, data.page_range)
        elif data.export_format == "zip":
            filepath = await export_service.export_book_with_images(db, data.book_id, data.page_range)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {data.export_format}")

        return {
            "file_path": filepath,
            "filename": os.path.basename(filepath),
            "file_size": os.path.getsize(filepath),
            "download_url": f"/api/export/download/{os.path.basename(filepath)}",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/download/{filename}", summary="下载导出文件")
async def download_export(filename: str):
    from app.config import EXPORTS_DIR
    filepath = os.path.join(EXPORTS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath, filename=filename)

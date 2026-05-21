from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.umiocr_client import umiocr_client
from app.schemas import UmiOcrStatus, SearchQuery, SearchResult

router = APIRouter(prefix="/api/ocr", tags=["OCR服务"])


class OcrRequest(BaseModel):
    base64: str
    options: dict = None


@router.post("", summary="快速OCR识别")
async def quick_ocr(req: OcrRequest):
    opts = req.options or {}
    result = await umiocr_client.recognize_image(
        image_base64=req.base64,
        language=opts.get("ocr.language", "简体中文"),
        tbpu_parser=opts.get("tbpu.parser", "multi_para"),
        data_format=opts.get("data.format", "text"),
    )
    return result


@router.get("/status", response_model=UmiOcrStatus, summary="检查UmiOCR服务状态")
async def check_ocr_status():
    available = await umiocr_client.check_available()
    return UmiOcrStatus(
        available=available,
        url=umiocr_client.base_url,
        version=None,
    )


@router.get("/options", summary="获取OCR配置选项")
async def get_ocr_options():
    return await umiocr_client.get_ocr_options()


@router.post("/search", response_model=list[SearchResult], summary="全文检索")
async def search_text(query: SearchQuery, db: AsyncSession = Depends(get_db)):
    from app.services import book_service
    results = await book_service.search_text(db, query.keyword, query.book_id, query.category)
    return results

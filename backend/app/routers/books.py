import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import book_service
from app.schemas import BookCreate, BookUpdate, BookResponse, PageResponse, PageTextUpdate, OcrTaskCreate, OcrTaskResponse

router = APIRouter(prefix="/api/books", tags=["图书管理"])


@router.post("", response_model=BookResponse, summary="创建图书")
async def create_book(data: BookCreate, db: AsyncSession = Depends(get_db)):
    book = await book_service.create_book(db, data)
    return book


@router.get("", summary="获取图书列表")
async def get_books(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    books, total = await book_service.get_books(db, skip, limit, status, category, keyword)
    return {"items": books, "total": total, "skip": skip, "limit": limit}


@router.get("/stats", summary="获取统计信息")
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await book_service.get_stats(db)


@router.get("/categories", summary="获取分类列表")
async def get_categories(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func
    from app.models import Book
    result = await db.execute(select(Book.category, func.count(Book.id)).group_by(Book.category))
    return [{"category": row[0], "count": row[1]} for row in result.all()]


@router.get("/{book_id}", response_model=BookResponse, summary="获取图书详情")
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    book = await book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    return book


@router.put("/{book_id}", response_model=BookResponse, summary="更新图书信息")
async def update_book(book_id: int, data: BookUpdate, db: AsyncSession = Depends(get_db)):
    book = await book_service.update_book(db, book_id, data)
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    return book


@router.delete("/{book_id}", summary="删除图书")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    success = await book_service.delete_book(db, book_id)
    if not success:
        raise HTTPException(status_code=404, detail="图书不存在")
    return {"message": "删除成功"}


@router.post("/{book_id}/pages", summary="导入页面图片")
async def import_pages(
    book_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")
    count = await book_service.import_pages(db, book_id, [content])
    return {"imported": count}


@router.get("/{book_id}/pages", summary="获取页面列表")
async def get_pages(
    book_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    pages, total = await book_service.get_pages(db, book_id, skip, limit)
    return {"items": pages, "total": total, "skip": skip, "limit": limit}


@router.get("/{book_id}/pages/{page_id}", response_model=PageResponse, summary="获取页面详情")
async def get_page(page_id: int, db: AsyncSession = Depends(get_db)):
    page = await book_service.get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    return page


@router.put("/{book_id}/pages/{page_id}/text", response_model=PageResponse, summary="更新页面OCR文本")
async def update_page_text(page_id: int, data: PageTextUpdate, db: AsyncSession = Depends(get_db)):
    page = await book_service.update_page_text(db, page_id, data.ocr_text)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    return page


@router.delete("/{book_id}/pages/{page_id}", summary="删除页面")
async def delete_page(book_id: int, page_id: int, db: AsyncSession = Depends(get_db)):
    success = await book_service.delete_page(db, book_id, page_id)
    if not success:
        raise HTTPException(status_code=404, detail="页面不存在")
    return {"message": "页面已删除"}


@router.post("/{book_id}/ocr", response_model=OcrTaskResponse, summary="启动OCR识别任务")
async def run_ocr(book_id: int, data: OcrTaskCreate, db: AsyncSession = Depends(get_db)):
    try:
        task = await book_service.run_ocr_task(
            db, book_id, data.ocr_language, data.tbpu_parser
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{book_id}/tasks", summary="获取图书OCR任务列表")
async def get_book_tasks(book_id: int, db: AsyncSession = Depends(get_db)):
    tasks = await book_service.get_book_tasks(db, book_id)
    return tasks


@router.get("/{book_id}/cover", summary="获取图书封面")
async def get_book_cover(book_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse
    book = await book_service.get_book(db, book_id)
    if not book or not book.cover_image:
        raise HTTPException(status_code=404, detail="封面不存在")
    return FileResponse(book.cover_image)


@router.get("/{book_id}/pages/{page_id}/image", summary="获取页面原图")
async def get_page_image(page_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse
    page = await book_service.get_page(db, page_id)
    if not page or not page.image_path or not os.path.exists(page.image_path):
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(page.image_path)


@router.get("/{book_id}/pages/{page_id}/thumbnail", summary="获取页面缩略图")
async def get_page_thumbnail(page_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse
    page = await book_service.get_page(db, page_id)
    if not page or not page.thumbnail_path or not os.path.exists(page.thumbnail_path):
        raise HTTPException(status_code=404, detail="缩略图不存在")
    return FileResponse(page.thumbnail_path)


@router.put("/{book_id}/pages/{page_id}/review", summary="切换页面校对状态")
async def toggle_page_reviewed(
    book_id: int,
    page_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await book_service.toggle_page_review(db, page_id)
    if result is None:
        raise HTTPException(status_code=404, detail="页面不存在")
    return {"reviewed": result}


@router.post("/{book_id}/complete", summary="标记图书校对完成")
async def complete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    success = await book_service.complete_book_review(db, book_id)
    if not success:
        raise HTTPException(status_code=404, detail="图书不存在")
    return {"message": "图书已标记为完成"}

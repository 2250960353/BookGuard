from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import book_service

router = APIRouter(prefix="/api/recycle", tags=["回收站"])


@router.get("", summary="获取已删除图书列表")
async def list_deleted_books(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    books, total = await book_service.get_deleted_books(db, skip, limit, keyword)
    return {"items": books, "total": total, "skip": skip, "limit": limit}


@router.get("/pages", summary="获取已删除页面列表（属于未删除的图书）")
async def list_deleted_pages(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    pages, total = await book_service.get_deleted_pages(db, skip, limit, keyword)
    return {"items": pages, "total": total, "skip": skip, "limit": limit}


@router.post("/pages/{page_id}/restore", summary="恢复页面")
async def restore_page(page_id: int, db: AsyncSession = Depends(get_db)):
    success = await book_service.restore_page(db, page_id)
    if not success:
        raise HTTPException(status_code=404, detail="页面不存在、未被删除或所属图书已被删除")
    return {"message": "页面已恢复"}


@router.delete("/pages/{page_id}", summary="永久删除页面")
async def permanent_delete_page(page_id: int, db: AsyncSession = Depends(get_db)):
    success = await book_service.permanent_delete_page(db, page_id)
    if not success:
        raise HTTPException(status_code=404, detail="页面不存在或未在回收站中")
    return {"message": "页面已永久删除"}


@router.post("/{book_id}/restore", summary="恢复图书")
async def restore_book(book_id: int, db: AsyncSession = Depends(get_db)):
    success = await book_service.restore_book(db, book_id)
    if not success:
        raise HTTPException(status_code=404, detail="图书不存在或未被删除")
    return {"message": "图书已恢复"}


@router.delete("/{book_id}", summary="永久删除图书")
async def permanent_delete(book_id: int, db: AsyncSession = Depends(get_db)):
    success = await book_service.permanent_delete_book(db, book_id)
    if not success:
        raise HTTPException(status_code=404, detail="图书不存在或未在回收站中")
    return {"message": "图书已永久删除"}

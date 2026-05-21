import os
import json
import zipfile
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Book, Page, ExportRecord
from app.config import EXPORTS_DIR, BOOKS_DIR
from app.schemas import PageStatus


async def export_book_txt(db: AsyncSession, book_id: int, page_range: Optional[List[int]] = None) -> str:
    book = await db.execute(select(Book).where(Book.id == book_id))
    book = book.scalar_one_or_none()
    if not book:
        raise ValueError("图书不存在")

    query = select(Page).where(Page.book_id == book_id, Page.status == PageStatus.COMPLETED.value)
    if page_range:
        query = query.where(Page.page_number.in_(page_range))
    query = query.order_by(Page.page_number)
    result = await db.execute(query)
    pages = result.scalars().all()

    lines = []
    lines.append(f"书名：{book.title}")
    lines.append(f"作者：{book.author}")
    if book.dynasty:
        lines.append(f"朝代：{book.dynasty}")
    if book.category:
        lines.append(f"分类：{book.category}")
    lines.append(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    for page in pages:
        lines.append(f"--- 第 {page.page_number} 页 ---")
        lines.append(page.ocr_text or "")
        lines.append("")

    content = "\n".join(lines)
    filename = f"{book.title}_文字版_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    filepath = os.path.join(EXPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    record = ExportRecord(
        book_id=book_id,
        export_format="txt",
        file_path=filepath,
        file_size=os.path.getsize(filepath),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return filepath


async def export_book_json(db: AsyncSession, book_id: int, page_range: Optional[List[int]] = None) -> str:
    book = await db.execute(select(Book).where(Book.id == book_id))
    book = book.scalar_one_or_none()
    if not book:
        raise ValueError("图书不存在")

    query = select(Page).where(Page.book_id == book_id, Page.status == PageStatus.COMPLETED.value)
    if page_range:
        query = query.where(Page.page_number.in_(page_range))
    query = query.order_by(Page.page_number)
    result = await db.execute(query)
    pages = result.scalars().all()

    data = {
        "book": {
            "title": book.title,
            "author": book.author,
            "dynasty": book.dynasty,
            "category": book.category,
            "language": book.language,
            "description": book.description,
            "is_handwritten": book.is_handwritten,
            "total_pages": book.total_pages,
        },
        "pages": [
            {
                "page_number": p.page_number,
                "ocr_text": p.ocr_text,
                "confidence": p.confidence,
                "is_handwritten": p.is_handwritten,
            }
            for p in pages
        ],
        "export_time": datetime.now().isoformat(),
    }

    content = json.dumps(data, ensure_ascii=False, indent=2)
    filename = f"{book.title}_结构化_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    filepath = os.path.join(EXPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    record = ExportRecord(
        book_id=book_id,
        export_format="json",
        file_path=filepath,
        file_size=os.path.getsize(filepath),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return filepath


async def export_book_md(db: AsyncSession, book_id: int, page_range: Optional[List[int]] = None) -> str:
    book = await db.execute(select(Book).where(Book.id == book_id))
    book = book.scalar_one_or_none()
    if not book:
        raise ValueError("图书不存在")

    query = select(Page).where(Page.book_id == book_id, Page.status == PageStatus.COMPLETED.value)
    if page_range:
        query = query.where(Page.page_number.in_(page_range))
    query = query.order_by(Page.page_number)
    result = await db.execute(query)
    pages = result.scalars().all()

    lines = []
    lines.append(f"# {book.title}")
    lines.append("")
    if book.author:
        lines.append(f"**作者**：{book.author}")
    if book.dynasty:
        lines.append(f"**朝代**：{book.dynasty}")
    if book.category:
        lines.append(f"**分类**：{book.category}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for page in pages:
        lines.append(f"## 第 {page.page_number} 页")
        lines.append("")
        lines.append(page.ocr_text or "")
        lines.append("")

    content = "\n".join(lines)
    filename = f"{book.title}_Markdown_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    filepath = os.path.join(EXPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    record = ExportRecord(
        book_id=book_id,
        export_format="md",
        file_path=filepath,
        file_size=os.path.getsize(filepath),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return filepath


async def export_book_with_images(db: AsyncSession, book_id: int, page_range: Optional[List[int]] = None) -> str:
    book = await db.execute(select(Book).where(Book.id == book_id))
    book = book.scalar_one_or_none()
    if not book:
        raise ValueError("图书不存在")

    query = select(Page).where(Page.book_id == book_id)
    if page_range:
        query = query.where(Page.page_number.in_(page_range))
    query = query.order_by(Page.page_number)
    result = await db.execute(query)
    pages = result.scalars().all()

    filename = f"{book.title}_图文包_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
    filepath = os.path.join(EXPORTS_DIR, filename)

    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        for page in pages:
            if page.image_path and os.path.exists(page.image_path):
                arcname = f"images/page_{page.page_number:04d}.png"
                zf.write(page.image_path, arcname)
            if page.ocr_text:
                text_name = f"texts/page_{page.page_number:04d}.txt"
                zf.writestr(text_name, page.ocr_text)

        metadata = {
            "title": book.title,
            "author": book.author,
            "dynasty": book.dynasty,
            "total_pages": book.total_pages,
            "export_time": datetime.now().isoformat(),
        }
        zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

    record = ExportRecord(
        book_id=book_id,
        export_format="zip",
        file_path=filepath,
        file_size=os.path.getsize(filepath),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return filepath

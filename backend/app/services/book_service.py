import os
import base64
import json
import asyncio
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from app.models import Book, Page, OcrTask
from app.schemas import BookCreate, BookUpdate, BookStatus, PageStatus, TaskStatus
from app.services.umiocr_client import umiocr_client
from app.config import BOOKS_DIR, OCR_RESULTS_DIR
from PIL import Image
import shutil


async def create_book(db: AsyncSession, data: BookCreate) -> Book:
    storage_path = os.path.join(BOOKS_DIR, f"book_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    os.makedirs(storage_path, exist_ok=True)
    os.makedirs(os.path.join(storage_path, "pages"), exist_ok=True)
    os.makedirs(os.path.join(storage_path, "thumbnails"), exist_ok=True)

    book = Book(
        title=data.title,
        author=data.author,
        dynasty=data.dynasty,
        category=data.category,
        language=data.language,
        description=data.description,
        is_handwritten=data.is_handwritten,
        source_type=data.source_type,
        storage_path=storage_path,
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


async def get_book(db: AsyncSession, book_id: int) -> Optional[Book]:
    result = await db.execute(select(Book).where(Book.id == book_id))
    return result.scalar_one_or_none()


async def get_books(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
) -> tuple:
    query = select(Book).where(Book.is_deleted == False)
    count_query = select(func.count(Book.id)).where(Book.is_deleted == False)

    if status:
        query = query.where(Book.status == status)
        count_query = count_query.where(Book.status == status)
    if category:
        query = query.where(Book.category == category)
        count_query = count_query.where(Book.category == category)
    if keyword:
        query = query.where(Book.title.contains(keyword))
        count_query = count_query.where(Book.title.contains(keyword))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Book.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    books = result.scalars().all()
    return books, total


async def update_book(db: AsyncSession, book_id: int, data: BookUpdate) -> Optional[Book]:
    book = await get_book(db, book_id)
    if not book:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(book, key, value)
    book.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(book)
    return book


async def delete_book(db: AsyncSession, book_id: int) -> bool:
    book = await get_book(db, book_id)
    if not book or book.is_deleted:
        return False
    book.is_deleted = True
    book.deleted_at = datetime.utcnow()
    book.updated_at = datetime.utcnow()
    await db.commit()
    return True


async def get_deleted_books(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    keyword: Optional[str] = None,
) -> tuple:
    query = select(Book).where(Book.is_deleted == True)
    count_query = select(func.count(Book.id)).where(Book.is_deleted == True)
    if keyword:
        query = query.where(Book.title.contains(keyword))
        count_query = count_query.where(Book.title.contains(keyword))
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    query = query.order_by(Book.deleted_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    books = result.scalars().all()
    return books, total


async def restore_book(db: AsyncSession, book_id: int) -> bool:
    book = await get_book(db, book_id)
    if not book or not book.is_deleted:
        return False
    book.is_deleted = False
    book.deleted_at = None
    book.updated_at = datetime.utcnow()
    await db.commit()
    return True


async def permanent_delete_book(db: AsyncSession, book_id: int) -> bool:
    book = await get_book(db, book_id)
    if not book or not book.is_deleted:
        return False
    if book.storage_path and os.path.exists(book.storage_path):
        shutil.rmtree(book.storage_path, ignore_errors=True)
    await db.delete(book)
    await db.commit()
    return True


async def import_pages(db: AsyncSession, book_id: int, image_files: List) -> int:
    book = await get_book(db, book_id)
    if not book:
        return 0

    storage_pages = os.path.join(book.storage_path, "pages")
    storage_thumbs = os.path.join(book.storage_path, "thumbnails")
    os.makedirs(storage_pages, exist_ok=True)
    os.makedirs(storage_thumbs, exist_ok=True)

    existing_count = book.total_pages
    imported = 0

    for idx, file_data in enumerate(image_files):
        page_num = existing_count + idx + 1
        filename = f"page_{page_num:04d}.png"
        thumb_filename = f"thumb_{page_num:04d}.png"

        file_path = os.path.join(storage_pages, filename)
        thumb_path = os.path.join(storage_thumbs, thumb_filename)

        if isinstance(file_data, bytes):
            with open(file_path, "wb") as f:
                f.write(file_data)
        elif isinstance(file_data, str) and os.path.isfile(file_data):
            shutil.copy2(file_data, file_path)
        else:
            continue

        try:
            img = Image.open(file_path)
            width, height = img.size
            img.thumbnail((300, 400))
            img.save(thumb_path)
        except Exception:
            width, height = 0, 0

        page = Page(
            book_id=book_id,
            page_number=page_num,
            image_path=file_path,
            thumbnail_path=thumb_path,
            image_width=width,
            image_height=height,
        )
        db.add(page)
        imported += 1

    book.total_pages = existing_count + imported
    if book.status == BookStatus.PENDING.value:
        book.status = BookStatus.SCANNING.value
    elif book.status == BookStatus.COMPLETED.value:
        book.status = BookStatus.REVIEWING.value
    book.updated_at = datetime.utcnow()
    await db.commit()
    return imported


async def get_pages(db: AsyncSession, book_id: int, skip: int = 0, limit: int = 50) -> tuple:
    count_result = await db.execute(
        select(func.count(Page.id)).where(Page.book_id == book_id, Page.is_deleted == False)
    )
    total = count_result.scalar()
    result = await db.execute(
        select(Page)
        .where(Page.book_id == book_id, Page.is_deleted == False)
        .order_by(Page.page_number)
        .offset(skip)
        .limit(limit)
    )
    pages = result.scalars().all()
    return pages, total


async def get_page(db: AsyncSession, page_id: int) -> Optional[Page]:
    result = await db.execute(select(Page).where(Page.id == page_id))
    return result.scalar_one_or_none()


async def update_page_text(db: AsyncSession, page_id: int, ocr_text: str) -> Optional[Page]:
    page = await get_page(db, page_id)
    if not page:
        return None
    page.ocr_text = ocr_text
    page.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(page)
    return page


async def toggle_page_review(db: AsyncSession, page_id: int) -> Optional[dict]:
    page = await get_page(db, page_id)
    if not page:
        return None
    was_reviewed = page.is_reviewed
    page.is_reviewed = not page.is_reviewed
    page.updated_at = datetime.utcnow()
    book_reverted = False
    if was_reviewed and not page.is_reviewed:
        book = await get_book(db, page.book_id)
        if book and book.status == BookStatus.COMPLETED.value:
            book.status = BookStatus.REVIEWING.value
            book.updated_at = datetime.utcnow()
            book_reverted = True
    await db.commit()
    return {"reviewed": page.is_reviewed, "book_reverted": book_reverted}


async def delete_page(db: AsyncSession, book_id: int, page_id: int) -> bool:
    page = await get_page(db, page_id)
    if not page or page.book_id != book_id or page.is_deleted:
        return False

    page.is_deleted = True
    page.deleted_at = datetime.utcnow()
    page.updated_at = datetime.utcnow()

    book = await get_book(db, book_id)
    if book and book.total_pages > 0:
        book.total_pages -= 1
        if page.status == PageStatus.COMPLETED.value and book.recognized_pages > 0:
            book.recognized_pages -= 1
        book.updated_at = datetime.utcnow()

    await db.commit()
    return True


async def get_deleted_pages(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    keyword: str = None,
) -> tuple:
    query = (
        select(Page, Book.title.label("book_title"))
        .join(Book, Page.book_id == Book.id)
        .where(Page.is_deleted == True, Book.is_deleted == False)
    )
    count_query = (
        select(func.count(Page.id))
        .join(Book, Page.book_id == Book.id)
        .where(Page.is_deleted == True, Book.is_deleted == False)
    )
    if keyword:
        query = query.where(Book.title.contains(keyword))
        count_query = count_query.where(Book.title.contains(keyword))
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    query = query.order_by(Page.deleted_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    pages = []
    for row in rows:
        p = row[0]
        pages.append({
            "id": p.id,
            "book_id": p.book_id,
            "page_number": p.page_number,
            "status": p.status,
            "ocr_text": p.ocr_text,
            "confidence": p.confidence,
            "is_reviewed": p.is_reviewed,
            "deleted_at": p.deleted_at.isoformat() if p.deleted_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "book_title": row[1],
        })
    return pages, total


async def restore_page(db: AsyncSession, page_id: int) -> bool:
    page = await get_page(db, page_id)
    if not page or not page.is_deleted:
        return False
    book = await get_book(db, page.book_id)
    if not book or book.is_deleted:
        return False
    page.is_deleted = False
    page.deleted_at = None
    page.updated_at = datetime.utcnow()
    if book:
        book.total_pages += 1
        if page.status == PageStatus.COMPLETED.value:
            book.recognized_pages += 1
        book.updated_at = datetime.utcnow()
    await db.commit()
    return True


async def permanent_delete_page(db: AsyncSession, page_id: int) -> bool:
    page = await get_page(db, page_id)
    if not page or not page.is_deleted:
        return False
    if page.image_path and os.path.exists(page.image_path):
        os.remove(page.image_path)
    if page.thumbnail_path and os.path.exists(page.thumbnail_path):
        os.remove(page.thumbnail_path)
    await db.delete(page)
    await db.commit()
    return True


async def complete_book_review(db: AsyncSession, book_id: int) -> bool:
    book = await get_book(db, book_id)
    if not book:
        return False
    book.status = BookStatus.COMPLETED.value
    book.updated_at = datetime.utcnow()
    await db.commit()
    return True


async def run_ocr_task(db: AsyncSession, book_id: int, language: str = "简体中文", tbpu_parser: str = "multi_para") -> OcrTask:
    book = await get_book(db, book_id)
    if not book:
        raise ValueError("图书不存在")

    result = await db.execute(
        select(Page).where(Page.book_id == book_id).order_by(Page.page_number)
    )
    pages = result.scalars().all()

    task = OcrTask(
        book_id=book_id,
        task_type="ocr",
        status=TaskStatus.RUNNING.value,
        total_pages=len(pages),
        ocr_language=language,
        tbpu_parser=tbpu_parser,
        started_at=datetime.utcnow(),
    )
    db.add(task)

    book.status = BookStatus.RECOGNIZING.value
    await db.commit()
    await db.refresh(task)

    asyncio.create_task(_execute_ocr(db, task.id, pages, language, tbpu_parser))
    return task


async def _execute_ocr(db: AsyncSession, task_id: int, pages: List[Page], language: str, tbpu_parser: str):
    from app.database import async_session

    processed = 0
    total_confidence = 0.0
    total_pages = len(pages)

    async with async_session() as session:
        for page in pages:
            try:
                if not page.image_path or not os.path.exists(page.image_path):
                    async with session.begin():
                        await session.execute(
                            update(Page).where(Page.id == page.id).values(status=PageStatus.FAILED.value)
                        )
                    processed += 1
                    continue

                start_time = datetime.utcnow()
                result = await umiocr_client.recognize_image_file(
                    page.image_path, language=language, tbpu_parser=tbpu_parser
                )
                processing_time = (datetime.utcnow() - start_time).total_seconds()

                async with session.begin():
                    if result.get("code") == 100:
                        data = result.get("data", [])
                        text_parts = []
                        confidence_sum = 0.0
                        count = 0
                        for item in data:
                            text_parts.append(item.get("text", ""))
                            confidence_sum += item.get("score", 0)
                            count += 1
                        avg_conf = confidence_sum / count if count > 0 else 0
                        total_confidence += avg_conf

                        ocr_text = "\n".join(text_parts)
                        await session.execute(
                            update(Page)
                            .where(Page.id == page.id)
                            .values(
                                ocr_text=ocr_text,
                                ocr_raw=json.dumps(data, ensure_ascii=False),
                                confidence=avg_conf,
                                status=PageStatus.COMPLETED.value,
                                processing_time=processing_time,
                                updated_at=datetime.utcnow(),
                            )
                        )
                    elif result.get("code") == 101:
                        await session.execute(
                            update(Page)
                            .where(Page.id == page.id)
                            .values(
                                ocr_text="",
                                status=PageStatus.COMPLETED.value,
                                processing_time=processing_time,
                                updated_at=datetime.utcnow(),
                            )
                        )
                    else:
                        await session.execute(
                            update(Page)
                            .where(Page.id == page.id)
                            .values(
                                status=PageStatus.FAILED.value,
                                processing_time=processing_time,
                                updated_at=datetime.utcnow(),
                            )
                        )

                    processed += 1
                    progress = processed / total_pages if total_pages > 0 else 0
                    await session.execute(
                        update(OcrTask)
                        .where(OcrTask.id == task_id)
                        .values(processed_pages=processed, progress=progress)
                    )

            except Exception as e:
                processed += 1
                async with session.begin():
                    await session.execute(
                        update(Page).where(Page.id == page.id).values(status=PageStatus.FAILED.value)
                    )

        avg_conf = total_confidence / processed if processed > 0 else 0
        completed_count = 0
        async with session.begin():
            result = await session.execute(
                select(func.count(Page.id)).where(
                    Page.book_id == pages[0].book_id if pages else 0,
                    Page.status == PageStatus.COMPLETED.value,
                )
            )
            completed_count = result.scalar()

            await session.execute(
                update(OcrTask)
                .where(OcrTask.id == task_id)
                .values(
                    status=TaskStatus.COMPLETED.value,
                    progress=1.0,
                    processed_pages=processed,
                    completed_at=datetime.utcnow(),
                )
            )

            await session.execute(
                update(Book)
                .where(Book.id == pages[0].book_id if pages else 0)
                .values(
                    recognized_pages=completed_count,
                    avg_confidence=avg_conf,
                    status=BookStatus.REVIEWING.value,
                    updated_at=datetime.utcnow(),
                )
            )


async def get_ocr_task(db: AsyncSession, task_id: int) -> Optional[OcrTask]:
    result = await db.execute(select(OcrTask).where(OcrTask.id == task_id))
    return result.scalar_one_or_none()


async def get_book_tasks(db: AsyncSession, book_id: int) -> List[OcrTask]:
    result = await db.execute(
        select(OcrTask).where(OcrTask.book_id == book_id).order_by(OcrTask.created_at.desc())
    )
    return result.scalars().all()


async def search_text(db: AsyncSession, keyword: str, book_id: Optional[int] = None, category: Optional[str] = None) -> list:
    query = (
        select(Page, Book.title.label("book_title"))
        .join(Book, Page.book_id == Book.id)
        .where(Page.ocr_text.contains(keyword))
    )
    if book_id:
        query = query.where(Page.book_id == book_id)
    if category:
        query = query.where(Book.category == category)

    result = await db.execute(query.limit(100))
    rows = result.all()
    results = []
    for row in rows:
        page = row[0]
        book_title = row[1]
        text = page.ocr_text or ""
        idx = text.find(keyword)
        start = max(0, idx - 30)
        end = min(len(text), idx + len(keyword) + 30)
        highlight = text[start:end]
        results.append({
            "book_id": page.book_id,
            "book_title": book_title,
            "page_id": page.id,
            "page_number": page.page_number,
            "ocr_text": text,
            "confidence": page.confidence,
            "highlight": f"...{highlight}...",
        })
    return results


async def get_stats(db: AsyncSession) -> dict:
    total_books = (await db.execute(select(func.count(Book.id)))).scalar()
    total_pages = (await db.execute(select(func.count(Page.id)))).scalar()
    recognized_pages = (
        await db.execute(select(func.count(Page.id)).where(Page.status == PageStatus.COMPLETED.value))
    ).scalar()
    avg_conf = (await db.execute(select(func.avg(Page.confidence)).where(Page.confidence > 0))).scalar() or 0

    status_result = await db.execute(select(Book.status, func.count(Book.id)).group_by(Book.status))
    books_by_status = {row[0]: row[1] for row in status_result.all()}

    category_result = await db.execute(select(Book.category, func.count(Book.id)).group_by(Book.category))
    books_by_category = {row[0]: row[1] for row in category_result.all()}

    return {
        "total_books": total_books,
        "total_pages": total_pages,
        "recognized_pages": recognized_pages,
        "avg_confidence": round(avg_conf, 4),
        "books_by_status": books_by_status,
        "books_by_category": books_by_category,
    }

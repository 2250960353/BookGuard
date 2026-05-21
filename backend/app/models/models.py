from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class BookStatus(str, enum.Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    RECOGNIZING = "recognizing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    author = Column(String(200), default="")
    dynasty = Column(String(100), default="")
    category = Column(String(100), default="")
    language = Column(String(50), default="简体中文")
    description = Column(Text, default="")
    status = Column(String(20), default=BookStatus.PENDING.value)
    cover_image = Column(String(500), default="")
    total_pages = Column(Integer, default=0)
    recognized_pages = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    is_handwritten = Column(Boolean, default=False)
    source_type = Column(String(50), default="scan")
    storage_path = Column(String(500), default="")
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pages = relationship("Page", back_populates="book", cascade="all, delete-orphan")
    ocr_tasks = relationship("OcrTask", back_populates="book", cascade="all, delete-orphan")


class PageStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_path = Column(String(500), default="")
    thumbnail_path = Column(String(500), default="")
    ocr_text = Column(Text, default="")
    ocr_raw = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    status = Column(String(20), default=PageStatus.PENDING.value)
    is_handwritten = Column(Boolean, default=False)
    is_reviewed = Column(Boolean, default=False)
    image_width = Column(Integer, default=0)
    image_height = Column(Integer, default=0)
    processing_time = Column(Float, default=0.0)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    book = relationship("Book", back_populates="pages")


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OcrTask(Base):
    __tablename__ = "ocr_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String(50), default="ocr")
    status = Column(String(20), default=TaskStatus.PENDING.value)
    total_pages = Column(Integer, default=0)
    processed_pages = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    ocr_engine = Column(String(100), default="RapidOCR")
    ocr_language = Column(String(50), default="简体中文")
    tbpu_parser = Column(String(50), default="multi_para")
    error_message = Column(Text, default="")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="ocr_tasks")


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    real_name = Column(String(100), default="")
    role = Column(String(20), default=UserRole.OPERATOR.value)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExportRecord(Base):
    __tablename__ = "export_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    export_format = Column(String(50), nullable=False)
    file_path = Column(String(500), default="")
    file_size = Column(Integer, default=0)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

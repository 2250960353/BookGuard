from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BookStatus(str, Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    RECOGNIZING = "recognizing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PageStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(default="", max_length=200)
    dynasty: str = Field(default="", max_length=100)
    category: str = Field(default="", max_length=100)
    language: str = Field(default="简体中文", max_length=50)
    description: str = Field(default="")
    is_handwritten: bool = Field(default=False)
    source_type: str = Field(default="scan")


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    author: Optional[str] = Field(default=None, max_length=200)
    dynasty: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    language: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    is_handwritten: Optional[bool] = None
    status: Optional[str] = None


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    dynasty: str
    category: str
    language: str
    description: str
    status: str
    cover_image: str
    total_pages: int
    recognized_pages: int
    avg_confidence: float
    is_handwritten: bool
    source_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PageResponse(BaseModel):
    id: int
    book_id: int
    page_number: int
    image_path: str
    thumbnail_path: str
    ocr_text: str
    confidence: float
    status: str
    is_handwritten: bool
    image_width: int
    image_height: int
    processing_time: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PageTextUpdate(BaseModel):
    ocr_text: str


class OcrTaskCreate(BaseModel):
    book_id: int
    ocr_language: str = Field(default="简体中文")
    tbpu_parser: str = Field(default="multi_para")
    page_range: Optional[List[int]] = None


class OcrTaskResponse(BaseModel):
    id: int
    book_id: int
    task_type: str
    status: str
    total_pages: int
    processed_pages: int
    progress: float
    ocr_engine: str
    ocr_language: str
    tbpu_parser: str
    error_message: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    real_name: str = Field(default="", max_length=100)
    role: UserRole = Field(default=UserRole.OPERATOR)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    real_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ExportRequest(BaseModel):
    book_id: int
    export_format: str = Field(default="txt")
    include_images: bool = Field(default=False)
    page_range: Optional[List[int]] = None


class ExportResponse(BaseModel):
    id: int
    book_id: int
    export_format: str
    file_path: str
    file_size: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    keyword: str = Field(..., min_length=1)
    book_id: Optional[int] = None
    category: Optional[str] = None
    page_number: Optional[int] = None


class SearchResult(BaseModel):
    book_id: int
    book_title: str
    page_id: int
    page_number: int
    ocr_text: str
    confidence: float
    highlight: str


class UmiOcrStatus(BaseModel):
    available: bool
    url: str
    version: Optional[str] = None


class StatsResponse(BaseModel):
    total_books: int
    total_pages: int
    recognized_pages: int
    avg_confidence: float
    books_by_status: dict
    books_by_category: dict

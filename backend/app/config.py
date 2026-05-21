import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
BOOKS_DIR = os.path.join(DATA_DIR, "books")
OCR_RESULTS_DIR = os.path.join(DATA_DIR, "ocr_results")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")

DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'bookguard.db')}"

UMIOCR_API_URL = os.getenv("UMIOCR_API_URL", "http://127.0.0.1:1224")

SECRET_KEY = os.getenv("SECRET_KEY", "bookguard-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

for d in [DATA_DIR, BOOKS_DIR, OCR_RESULTS_DIR, EXPORTS_DIR, UPLOADS_DIR]:
    os.makedirs(d, exist_ok=True)

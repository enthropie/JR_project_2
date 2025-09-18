from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.file_utils import is_allowed_file, MAX_FILE_SIZE, get_unique_name

# ===============================
# Настройки приложения
# ===============================
app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "all_images"
IMAGES_DIR.mkdir(exist_ok=True)

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/all_images", StaticFiles(directory=IMAGES_DIR), name="all_images")

templates = Jinja2Templates(directory="templates")

# --- Настройка логирования ---

# Настройка логов Uvicorn
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

# Хэндлер для файла
file_handler = RotatingFileHandler("logs/app.log", maxBytes=5_000_000, backupCount=5)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    "%Y-%m-%d %H:%M:%S"
))

# Хэндлер для консоли
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    "%Y-%m-%d %H:%M:%S"
))

# Добавляем оба
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ===============================
# Подключение к PostgreSQL
# ===============================
def get_db_connection():
    return psycopg2.connect(
        dbname="images_db",
        user="postgres",
        password="pass123456",
        host= "db",
        port="5432",
        cursor_factory=RealDictCursor
    )

# ===============================
# Вспомогательные функции
# ===============================
def save_metadata(filename, original_name, size, file_type):
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        INSERT INTO images (filename, original_name, size, file_type)
        VALUES (%s, %s, %s, %s)
    """
    cur.execute(query, (filename, original_name, size, file_type))
    conn.commit()
    cur.close()
    conn.close()

def get_images(limit: int, offset: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM images ORDER BY upload_time DESC LIMIT %s OFFSET %s",
        (limit, offset),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def count_images():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM images")
    total = cur.fetchone()["total"]
    cur.close()
    conn.close()
    return total

def delete_image_by_id(image_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM images WHERE id = %s", (image_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None

    filename = row["filename"]

    # Удаляем запись из базы
    cur.execute("DELETE FROM images WHERE id = %s", (image_id,))
    conn.commit()
    cur.close()
    conn.close()

    # Удаляем файл с диска
    file_path = IMAGES_DIR / filename
    if file_path.exists():
        file_path.unlink()

    return filename

# ===============================
# Маршруты
# ===============================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload/", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    my_file = Path(file.filename)

    # Проверяем расширение
    if not is_allowed_file(my_file):
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат файла")

    # Проверяем размер
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой")

    # Уникальное имя
    new_file_name = get_unique_name(my_file)
    save_path = IMAGES_DIR / new_file_name
    save_path.write_bytes(content)

    # Метаданные
    save_metadata(
        filename=new_file_name,
        original_name=file.filename,
        size=len(content),
        file_type=my_file.suffix.lower().replace(".", "")
    )

    return JSONResponse(content={"filename": new_file_name})

@app.get("/images-list", response_class=HTMLResponse)
async def images_list(request: Request, page: int = Query(1, ge=1)):
    per_page = 10
    offset = (page - 1) * per_page
    images = get_images(limit=per_page, offset=offset)
    total = count_images()
    total_pages = (total + per_page - 1) // per_page

    has_next = page < total_pages

    return templates.TemplateResponse("images.html", {
        "request": request,
        "images": images,
        "page": page,
        "total_pages": total_pages,
        "has_next": has_next
    })

@app.get("/delete/{image_id}")
async def delete_image(image_id: int, page: int = Query(1, ge=1)):
    filename = delete_image_by_id(image_id)
    if not filename:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    return RedirectResponse(url=f"/images-list?page={page}", status_code=303)

# ===============================
# Запуск
# ===============================
if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

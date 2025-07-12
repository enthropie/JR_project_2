from random import random
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.file_utils import is_allowed_file, MAX_FILE_SIZE, get_unique_name
import os



app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "all_images"

# Подключение папки static
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/all_images", StaticFiles(directory=IMAGES_DIR), name="all_images")


templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    files = [f.name for f in IMAGES_DIR.iterdir() if f.is_file()]
    return templates.TemplateResponse("index.html", {"request": request, "files": files})

@app.post("/delete/{filename}")
def delete_file(filename: str):
    file_path = IMAGES_DIR / filename
    if file_path.exists():
        file_path.unlink()
    return RedirectResponse("/images", status_code=303)

@app.get("/images/", response_class=HTMLResponse)
async def images(request: Request):
    files = [f.name for f in IMAGES_DIR.iterdir() if f.is_file()]
    return templates.TemplateResponse("images.html", {"request": request, "files": files})


@app.get("/upload/", response_class=HTMLResponse)
async def upload(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("upload.html", context=context)


@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    print(f"Файл {file.filename} получен")

    my_file = Path(file.filename)

    if is_allowed_file(my_file):
        print("Верное расширение файла")
    else:
        print("Не верное расширение файла")
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат. Разрешены только jpg, jpeg, png, gif")

    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой")

    new_file_name = get_unique_name(my_file)

    print(f"app.py {new_file_name}")

    image_dir = Path("all_images")
    image_dir.mkdir(exist_ok=True)
    save_path = image_dir / new_file_name

    save_path.write_bytes(content)

    print(f"{save_path=}")

    #return PlainTextResponse(f"POST запрос отработал и получили {file.filename}")
    return JSONResponse(content={"filename": new_file_name})


# uvicorn app:app --reload --host localhost --port 8001
if __name__ == '__main__':
    try:
        uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Сервер остановлен вручную.")
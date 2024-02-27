import asyncio
import hashlib
import json
import logging
import os
import pathlib
import sqlite3
from fastapi import UploadFile, FastAPI, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# json_file = "./items.json"
db = '../db/mercari.sqlite3'

def store_image(image: UploadFile = File(...)):
    # image.readでcoroutine objectが生成されていたためbinary dataを取り出すためにasyncio.runを追加
    image_bytes = asyncio.run(image.read())
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    image_filename = f"{image_hash}.jpg"

    # imageファイルを複数回保存しないようにするため(sha256より同じ画像には同じファイル名が生成されることがsecureされている)
    if os.path.isfile(image_filename):
        logger.info(f"{image_filename} exists.")
    else:
        with open(images / image_filename, "wb") as image_file:
            image_file.write(image_bytes)
        logger.info(f"Image saved: {image_filename}")
    
    return image_filename


@app.get("/")
def root():
    return {"message": "Hello, world!"}


@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}, {category}")

    # with open(json_file, mode='r') as j:
    #     items = json.load(j)
    
    # image_filename = store_image(image)
    
    # items['items'].append({'name': name, 'category': category, 'image_filename': image_filename})

    # with open(json_file, mode='w') as j:
    #     json.dump(items, j)
        
    # return {"message": f"item received: {name}, {category}, {image_filename}"}
    
    
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    image_filename = store_image(image)
    
    # add record into sqlite
    cur.execute('INSERT INTO items(name, category, image_name) VALUES(?, ?, ?)', (name, category, image_filename))

    conn.commit()

    # close cur
    cur.close()
    # close db
    conn.close()

    return {"message": f"item received: {name}, {category}, {image_filename}"}


@app.get("/items")
def get_items():
    # with open(json_file, mode='r') as getfile:
    #     items = json.load(getfile)
    # return items

    # connect to db
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # terminalで実行したSQL文と同じようにexecute()に書く
    cur.execute('SELECT * FROM items')
    # 中身を全て取得する = fetchall()
    get_data = cur.fetchall()

    # close cur
    cur.close()
    # close db
    conn.close()

    return get_data


@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)


@app.get("/items/{item_id}")
def get_item(item_id: int):
    with open(json_file, mode='r') as j:
        items = json.load(j)

    if item_id >= len(items['items']):
        raise HTTPException(status_code=404, detail="No item found with this id")
    
    else: 
        return items['items'][item_id - 1]


@app.get("/search")
def search_item(keyword: str):
    logger.info(f"Search item name: {keyword}")  # keyword探す

    # connect to db
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # 検索
    cur.execute('SELECT * FROM items WHERE name LIKE ?', (keyword,))
    # 中身を全て取得する = fetchall()
    get_data_search = cur.fetchall()

    # close cur
    cur.close()
    # close db
    conn.close()

    return get_data_search
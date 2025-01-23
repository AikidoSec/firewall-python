import aikido_zen  # Aikido package import
aikido_zen.protect()

import time
import asyncpg
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from aikido_zen.middleware import AikidoFastAPIMiddleware

templates = Jinja2Templates(directory="templates")

app = FastAPI()

# CORS middleware (optional, depending on your needs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AikidoFastAPIMiddleware)

async def get_db_connection():
    return await asyncpg.connect(
        host="localhost",
        database="db",
        user="user",
        password="password"
    )

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    conn = await get_db_connection()
    dogs = await conn.fetch("SELECT * FROM dogs")
    await conn.close()
    return templates.TemplateResponse('index.html', {"request": request, "title": 'Homepage', "dogs": dogs})

@app.get("/dogpage/{dog_id:int}", response_class=HTMLResponse)
async def get_dogpage(request: Request, dog_id: int):
    conn = await get_db_connection()
    dog = await conn.fetchrow("SELECT * FROM dogs WHERE id = $1", dog_id)
    await conn.close()
    if dog is None:
        raise HTTPException(status_code=404, detail="Dog not found")
    return templates.TemplateResponse('dogpage.html', {"request": request, "title": 'Dog', "dog": dog, "isAdmin": "Yes" if dog[2] else "No"})

@app.get("/create", response_class=HTMLResponse)
async def show_create_dog_form(request: Request):
    return templates.TemplateResponse('create_dog.html', {"request": request})

@app.post("/create")
async def create_dog(request: Request):
    data = await request.form()
    dog_name = data.get('dog_name')

    if not dog_name:
        return JSONResponse({"error": "dog_name is required"}, status_code=400)

    conn = await get_db_connection()
    try:
        await conn.execute("INSERT INTO dogs (dog_name, isAdmin) VALUES ($1, FALSE)", dog_name)
    finally:
        await conn.close()

    return JSONResponse({"message": f'Dog {dog_name} created successfully'}, status_code=201)

@app.get("/just")
async def just():
    return JSONResponse({"message": "Empty Page"})

@app.get("/test_ratelimiting_1")
async def just():
    return JSONResponse({"message": "Empty Page"})

@app.get("/delayed_route")
async def delayed_route():
    time.sleep(1/1000)  # Note: This will block the event loop; consider using asyncio.sleep instead
    return JSONResponse({"message": "Empty Page"})

@app.get("/sync_route")
def sync_route():
    data = {"message": "This is a non-async route!"}
    return JSONResponse(data)

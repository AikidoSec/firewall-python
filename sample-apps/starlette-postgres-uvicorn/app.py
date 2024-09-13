from dotenv import load_dotenv
import os
load_dotenv()
firewall_disabled = os.getenv("FIREWALL_DISABLED")
if firewall_disabled is not None:
    if firewall_disabled.lower() != "1":
        import aikido_zen  # Aikido package import
        aikido_zen.protect()

import asyncpg
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.templating import Jinja2Templates
from starlette.requests import Request

templates = Jinja2Templates(directory="templates")

async def get_db_connection():
    return await asyncpg.connect(
        host="host.docker.internal",
        database="db",
        user="user",
        password="password"
    )

async def homepage(request: Request):
    conn = await get_db_connection()
    dogs = await conn.fetch("SELECT * FROM dogs")
    await conn.close()
    return templates.TemplateResponse('index.html', {"request": request, "title": 'Homepage', "dogs": dogs})

async def get_dogpage(request: Request):
    dog_id = int(request.path_params['dog_id'])
    conn = await get_db_connection()
    dog = await conn.fetchrow("SELECT * FROM dogs WHERE id = $1", dog_id)
    await conn.close()
    return templates.TemplateResponse('dogpage.html', {"request": request, "title": 'Dog', "dog": dog, "isAdmin": "Yes" if dog[2] else "No"})

async def show_create_dog_form(request: Request):
    return templates.TemplateResponse('create_dog.html', {"request": request})

async def create_dog(request: Request):
    data = await request.form()
    dog_name = data.get('dog_name')

    if not dog_name:
        return JSONResponse({"error": "dog_name is required"}, status_code=400)

    conn = await get_db_connection()
    try:
        await conn.execute(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % (dog_name))
    finally:
        await conn.close()

    return JSONResponse({"message": f'Dog {dog_name} created successfully'}, status_code=201)

def sync_route(request):
    data = {"message": "This is a non-async route!"}
    return JSONResponse(data)

app = Starlette(routes=[
    Route("/", homepage),
    Route("/dogpage/{dog_id:int}", get_dogpage),
    Route("/create", show_create_dog_form, methods=["GET"]),
    Route("/create", create_dog, methods=["POST"]),
    Route("/sync_route", sync_route)
])

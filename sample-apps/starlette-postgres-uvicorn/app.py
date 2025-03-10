import aikido_zen  # Aikido package import
aikido_zen.protect()
import os

dont_add_middleware = os.getenv("DONT_ADD_MIDDLEWARE")
import time
import asyncpg
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.templating import Jinja2Templates
from starlette.requests import Request
from starlette.middleware import Middleware

templates = Jinja2Templates(directory="templates")

async def get_db_connection():
    return await asyncpg.connect(
        host="localhost",
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

async def just(request: Request):
    return JSONResponse({"message": "Empty Page"})

async def delayed_route(request: Request):
    time.sleep(1/1000)
    return JSONResponse({"message": "Empty Page"})

def sync_route(request):
    data = {"message": "This is a non-async route!"}
    return JSONResponse(data)
middleware = []
if dont_add_middleware is None or dont_add_middleware.lower() != "1":
    # Use DONT_ADD_MIDDLEWARE so we don't add this middleware during e.g. benchmarks.
    import aikido_zen
    from aikido_zen.middleware import AikidoStarletteMiddleware  # Aikido package import
    class SetUserMiddleware:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            for header, value in scope['headers']:
                if header.decode("utf-8").upper() == 'USER':
                    aikido_zen.set_user({"id": value.decode("utf-8"), "name": "John Doe"})
            return await self.app(scope, receive, send)
    middleware.append(Middleware(SetUserMiddleware))
    middleware.append(Middleware(AikidoStarletteMiddleware))



routes = [
    Route("/", homepage),
    Route("/dogpage/{dog_id:int}", get_dogpage),
    Route("/create", show_create_dog_form, methods=["GET"]),
    Route("/create", create_dog, methods=["POST"]),
    Route("/sync_route", sync_route),
    Route("/just", just,  methods=["GET"]),
    Route("/test_ratelimiting_1", just,  methods=["GET"]),
    Route("/delayed_route", delayed_route, methods=["GET"])
]
if len(middleware) != 0:
    app = Starlette(routes=routes, middleware=middleware)
else:
    app = Starlette(routes=routes)


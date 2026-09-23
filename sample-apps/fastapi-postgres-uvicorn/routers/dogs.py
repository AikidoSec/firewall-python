import asyncpg
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/dogs", tags=["dogs"])

templates = Jinja2Templates(directory="templates")


async def get_db_connection():
    return await asyncpg.connect(
        host="localhost",
        database="db",
        user="user",
        password="password",
    )


@router.get("/", response_class=HTMLResponse)
async def list_dogs(request: Request):
    conn = await get_db_connection()
    dogs = await conn.fetch("SELECT * FROM dogs")
    await conn.close()
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Dogs", "dogs": dogs}
    )


@router.get("/{dog_id}", response_class=HTMLResponse)
async def get_dog(request: Request, dog_id: int):
    conn = await get_db_connection()
    dog = await conn.fetchrow("SELECT * FROM dogs WHERE id = $1", dog_id)
    await conn.close()
    if dog is None:
        raise HTTPException(status_code=404, detail="Dog not found")
    return templates.TemplateResponse(
        "dogpage.html",
        {"request": request, "title": "Dog", "dog": dog, "isAdmin": "Yes" if dog[2] else "No"},
    )


@router.post("/")
async def create_dog(request: Request):
    data = await request.form()
    dog_name = data.get("dog_name")

    if not dog_name:
        return JSONResponse({"error": "dog_name is required"}, status_code=400)

    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO dogs (dog_name, isAdmin) VALUES ($1, FALSE)", dog_name
        )
    finally:
        await conn.close()

    return JSONResponse({"message": f"Dog {dog_name} created successfully"}, status_code=201)

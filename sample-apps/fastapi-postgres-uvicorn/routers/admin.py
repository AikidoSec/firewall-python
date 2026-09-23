import asyncpg
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_db_connection():
    return await asyncpg.connect(
        host="localhost",
        database="db",
        user="user",
        password="password",
    )


@router.get("/dogs")
async def list_admin_dogs():
    conn = await get_db_connection()
    dogs = await conn.fetch("SELECT * FROM dogs WHERE isAdmin = TRUE")
    await conn.close()
    return JSONResponse({"admin_dogs": [dict(d) for d in dogs]})


@router.delete("/dogs/{dog_id}")
async def delete_dog(dog_id: int):
    conn = await get_db_connection()
    result = await conn.execute("DELETE FROM dogs WHERE id = $1", dog_id)
    await conn.close()
    deleted = int(result.split()[-1])
    if deleted == 0:
        return JSONResponse({"error": "Dog not found"}, status_code=404)
    return JSONResponse({"message": f"Dog {dog_id} deleted"})

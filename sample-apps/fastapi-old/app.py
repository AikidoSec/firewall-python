import aikido_zen
aikido_zen.protect()

import subprocess
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from aikido_zen.middleware import AikidoFastAPIMiddleware

app = FastAPI()
app.add_middleware(AikidoFastAPIMiddleware)


@app.get("/")
async def homepage():
    return JSONResponse({"message": "Hello from old FastAPI"})


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return JSONResponse({"user_id": user_id, "name": "Test User"})


@app.post("/users")
async def create_user():
    return JSONResponse({"message": "User created"}, status_code=201)


@app.get("/sync_route")
def sync_route():
    return JSONResponse({"message": "This is a sync route"})


@app.get("/shell/{command}")
async def execute_command(command: str):
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return JSONResponse({"output": result.stdout})

from dotenv import load_dotenv
import os
import asyncpg
from quart import Quart, render_template, request, jsonify

load_dotenv()
firewall_disabled = os.getenv("FIREWALL_DISABLED")
if firewall_disabled is not None:
    if firewall_disabled.lower() != "1":
        import aikido_firewall  # Aikido package import
        aikido_firewall.protect()

app = Quart(__name__)

async def get_db_connection():
    return await asyncpg.connect(
        host="host.docker.internal",
        database="db",
        user="user",
        password="password"
    )

@app.route("/")
async def homepage():
    conn = await get_db_connection()
    dogs = await conn.fetch("SELECT * FROM dogs")
    await conn.close()
    return await render_template('index.html', title='Homepage', dogs=dogs)

@app.route('/dogpage/<int:dog_id>')
async def get_dogpage(dog_id):
    conn = await get_db_connection()
    dog = await conn.fetchrow("SELECT * FROM dogs WHERE id = $1", dog_id)
    await conn.close()
    return await render_template('dogpage.html', title='Dog', dog=dog, isAdmin=("Yes" if dog[2] else "No"))

@app.route("/create", methods=['GET'])
async def show_create_dog_form():
    return await render_template('create_dog.html')

@app.route("/create_many", methods=['GET'])
async def show_create_dog_form_many():
    return await render_template('create_dog.html')

@app.route("/create", methods=['POST'])
async def create_dog():
    data = await request.form
    dog_name = data.get('dog_name')

    if not dog_name:
        return jsonify({"error": "dog_name is required"}), 400

    conn = await get_db_connection()
    try:
        await conn.execute(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % (dog_name))

    finally:
        await conn.close()

    return jsonify({"message": f'Dog {dog_name} created successfully'}), 201

@app.route("/create_many", methods=['POST'])
async def create_dog_many():
    data = await request.form
    dog_name = data.get('dog_name')  # Expecting a list of dog names

    if not dog_name:
        return jsonify({"error": "dog_names must be a list and cannot be empty"}), 400

    conn = await get_db_connection()
    try:
        await conn.executemany(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', $1)" % (dog_name), [(False,), (False,), (False,)])
    finally:
        await conn.close()

    return jsonify({"message": f'{dog_name} created successfully'}), 201


if __name__ == '__main__':
    app.run()

import aikido_zen  # Aikido package import
aikido_zen.protect()

from quart import Quart, render_template, request, jsonify
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = Quart(__name__)

# MongoDB Connection :
client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
db = client["my_database"]
dogs = db["dogs"]

@app.route("/")
async def homepage():
    dog_array = dogs.find()
    return await render_template('index.html', title='Homepage', dogs=dog_array)


@app.route('/dogpage/<dog_id>')
async def get_dogpage(dog_id):
    dog = await dogs.find_one({"_id": ObjectId(dog_id)})
    return await render_template('dogpage.html', title="Dog", dog=dog)

@app.route("/create", methods=['GET'])
async def show_create_dog_form():
    return await render_template('create_dog.html')

@app.route("/create", methods=['POST'])
async def create_dog():
    data = await request.form
    new_dog = {
        'dog_name': data['dog_name'],
        'pswd': data['pswd']
    }
    res = await dogs.insert_one(new_dog)
    return jsonify({"message": f'Dog {res.inserted_id} created successfully'}), 201

@app.route("/auth", methods=['GET'])
async def show_auth_form():
    return await render_template('auth.html')

@app.route("/auth", methods=['POST'])
async def post_auth():
    data = await request.get_json()
    dog_info = {
        'dog_name': data.get('dog_name'),
        'pswd': data.get('pswd')
    }
    dog = await dogs.find_one(dog_info)
    if dog:
        dog_name = dog["dog_name"]
        return f'Dog with name {dog_name} authenticated successfully'
    else:
        return "Auth failed"

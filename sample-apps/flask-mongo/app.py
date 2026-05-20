import aikido_zen # Aikido package import
aikido_zen.protect()

import json
from flask import Flask, render_template, request
from flask_pymongo import PyMongo
from bson import ObjectId

app = Flask(__name__)
if __name__ == '__main__':
    app.run(threaded=True) # Run threaded so we can test how our bg process works
app.config["MONGO_URI"] = "mongodb://admin:password@localhost:27017/my_database?authSource=admin"
mongo = PyMongo(app)

@app.route("/")
def homepage():
    dogs = mongo.db.dogs.find()
    return render_template('index.html', title='Homepage', dogs=dogs)


@app.route('/dogpage/<dog_id>')
def get_dogpage(dog_id):
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    return render_template('dogpage.html', title=f'Dog', dog=dog)

@app.route("/create", methods=['GET'])
def show_create_dog_form():
    return render_template('create_dog.html')

@app.route("/create", methods=['POST'])
def create_dog():
    new_dog = {
        'dog_name': request.form['dog_name'],
        'pswd': request.form['pswd']
    }
    res = mongo.db.dogs.insert_one(new_dog)
    return f'Dog with id {res.inserted_id} created successfully'

@app.route("/auth", methods=['GET'])
def show_auth_form():
    return render_template('auth.html')

@app.route("/auth", methods=['POST'])
def post_auth():
    data = request.get_json()
    dog_info = {
        'dog_name': data.get('dog_name'),
        'pswd': data.get('pswd')
    }
    dog = mongo.db.dogs.find_one(dog_info)
    if dog:
        dog_name = dog["dog_name"]
        return f'Dog with name {dog_name} authenticated successfully'
    else:
        return f'Auth failed'

@app.route("/auth_force", methods=['POST'])
def post_auth2():
    data = request.get_json(force=True)
    dog_info = {
        'dog_name': data.get('dog_name'),
        'pswd': data.get('pswd')
    }
    dog = mongo.db.dogs.find_one(dog_info)
    if dog:
        dog_name = dog["dog_name"]
        return f'Dog with name {dog_name} authenticated successfully'
    else:
        return f'Auth failed'


# --- bypass regression endpoints ---

@app.route("/read", methods=['POST'])
def read_file():
    # Passes the raw bytes body directly to open() — path traversal sink.
    # Used by AIKIDO-5RDTZW1V regression test: a leading \xff byte must not
    # prevent the firewall from detecting the traversal in the rest of the path.
    with open(request.data) as f:
        return f.read()


@app.route("/auth-raw", methods=['POST'])
def post_auth_raw():
    # Parses the body via json.loads(bytes) without relying on Content-Type.
    # Used by AIKIDO-B3YABOSP regression test: surrogate bytes (\xed\xa0\x80)
    # embedded in the JSON body must not prevent the firewall from parsing the
    # body and detecting the NoSQL injection payload.
    data = json.loads(request.data)
    dog_info = {
        'dog_name': data.get('dog_name'),
        'pswd': data.get('pswd'),
    }
    dog = mongo.db.dogs.find_one(dog_info)
    if dog:
        return f'Dog with name {dog["dog_name"]} authenticated successfully'
    return 'Auth failed'

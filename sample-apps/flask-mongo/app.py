import aikido_firewall # Aikido package import
aikido_firewall.protect()

import json
from flask import Flask, render_template, request
from flask_pymongo import PyMongo
from bson import ObjectId
import subprocess
import sys
import requests

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://root:password@127.0.0.1:27017/app?authSource=admin"
mongo = PyMongo(app)

if __name__ == '__main__':
    app.run(host='127.0.0.1', threaded=True) # Run threaded so we can test how our bg process works

@app.route("/")
def homepage():
    dogs = mongo.db.dogs.find()
    print(dogs)
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

@app.route("/shell", methods=['GET'])
def show_auth_form2():
    print(request.cookies)
    print(request.cookies.get("hi"))
    call = requests.get("http://" + request.cookies.get("hi"))
    return str(call.status_code)

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

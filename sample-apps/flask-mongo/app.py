import aikido_firewall # Aikido package import
aikido_firewall.protect()

from flask import Flask, render_template, request
from flask_pymongo import PyMongo

app = Flask(__name__)
if __name__ == '__main__':
    app.run(threaded=True) # Run threaded so we can test our agent's capabilities
app.config["MONGO_URI"] = "mongodb://admin:password@db:27017/"
mongo = PyMongo(app)

@app.route("/")
def homepage():
    print(dir(mongo.db))
    dogs = mongo.db.dogs.find()
    return render_template('index.html', title='Homepage', dogs=dogs)


@app.route('/dogpage/<int:dog_id>')
def get_dogpage(dog_id):
    dog = mongo.dogs.find({id: str(dog_id)})
    return render_template('dogpage.html', title=f'Dog', dog=dog, isAdmin=("Yes" if dog[2] else "No"))

@app.route("/create", methods=['GET'])
def show_create_dog_form():
    return render_template('create_dog.html')

@app.route("/create", methods=['POST'])
def create_dog():
    dog_name = request.form['dog_name']
    return f'Dog {dog_name} created successfully'

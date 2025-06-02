import aikido_zen  # Aikido package import
aikido_zen.protect()

from flask import Flask, render_template, request
from clickhouse_driver import Client

app = Flask(__name__)

# Configure ClickHouse client
clickhouse_client = Client(host='127.0.0.1', port=9000, user='default', password='', database='default')

@app.route("/")
def homepage():
    # Fetch all dogs from ClickHouse
    dogs = clickhouse_client.execute("SELECT * FROM dogs")
    return render_template('index.html', title='Homepage', dogs=dogs)

@app.route('/dogpage/<string:dog_id>')
def get_dogpage(dog_id):
    # Fetch a specific dog by ID from ClickHouse
    dog = clickhouse_client.execute("SELECT * FROM dogs WHERE id = '{}'".format(dog_id))
    if dog:
        dog = dog[0]  # Get the first result
        return render_template('dogpage.html', title='Dog', dog=dog, isAdmin=("Yes" if dog[2] else "No"))
    else:
        return "Dog not found", 404

@app.route("/create", methods=['GET'])
def show_create_dog_form():
    return render_template('create_dog.html')

@app.route("/create", methods=['POST'])
def create_dog():
    dog_name = request.form['dog_name']
    # Insert a new dog into ClickHouse
    clickhouse_client.execute("INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name))
    return f'Dog {dog_name} created successfully'

if __name__ == '__main__':
    app.run()

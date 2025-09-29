import aikido_zen # Aikido package import
aikido_zen.protect()

import time
from flask import Flask, render_template, request
from flaskext.mysql import MySQL

app = Flask(__name__)

mysql = MySQL()
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
app.config['MYSQL_DATABASE_USER'] = 'user'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'db'
mysql.init_app(app)

@app.route("/")
def homepage():
    cursor = mysql.get_db().cursor()
    cursor.execute("SELECT * FROM db.dogs")
    dogs = cursor.fetchall()
    return render_template('index.html', title='Homepage', dogs=dogs)


@app.route('/dogpage/<int:dog_id>')
def get_dogpage(dog_id):
    cursor = mysql.get_db().cursor()
    cursor.execute("SELECT * FROM db.dogs WHERE id = " + str(dog_id))
    dog = cursor.fetchmany(1)[0]
    return render_template('dogpage.html', title=f'Dog', dog=dog, isAdmin=("Yes" if dog[2] else "No"))

@app.route("/create", methods=['GET'])
def show_create_dog_form():
    return render_template('create_dog.html')

@app.route("/create", methods=['POST'])
def create_dog():
    dog_name = request.form['dog_name']
    connection = mysql.get_db()
    cursor = connection.cursor()
    cursor.execute(f'INSERT INTO dogs (dog_name, isAdmin) VALUES ("%s", 0)' % (dog_name))
    connection.commit()
    return f'Dog {dog_name} created successfully'

@app.route("/benchmark", methods=['GET'])
def benchmark():
    time.sleep(1/1000)
    return "OK"


@app.route("/benchmark_io", methods=['GET'])
def benchmark_io():
    for i in range(1000):
        with open("benchmark_temp.txt", "w") as f:
            f.write("This is a benchmark file.")
        with open("benchmark_temp.txt", "r") as f:
            content = f.read()
    return "OK"

if __name__ == '__main__':
    app.run()

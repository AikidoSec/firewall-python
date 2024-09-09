import os
firewall_disabled = os.getenv("FIREWALL_DISABLED")
if firewall_disabled is not None:
    if firewall_disabled.lower() != "1":
        import aikido_zen # Aikido package import
        aikido_zen.protect()

import subprocess
from flask import Flask, render_template, request
from flaskext.mysql import MySQL
import requests
import subprocess

app = Flask(__name__)
if __name__ == '__main__':
    app.run()
mysql = MySQL()

app.config['MYSQL_DATABASE_HOST'] = 'host.docker.internal'
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

@app.route("/multiple_queries", methods=['POST'])
def multiple_queries():
    dog_name = request.form['dog_name']
    cursor = mysql.get_db().cursor()
    for i in range(20):
        cursor.execute(f'SELECT * FROM db.dogs WHERE dog_name = "%s"' % (dog_name))
        cursor.fetchmany(1)
    return f'OK'

@app.route("/create", methods=['POST'])
def create_dog():
    dog_name = request.form['dog_name']
    connection = mysql.get_db()
    cursor = connection.cursor()
    cursor.execute(f'INSERT INTO dogs (dog_name, isAdmin) VALUES ("%s", 0)' % (dog_name))
    connection.commit()
    return f'Dog {dog_name} created successfully'

@app.route("/shell", methods=['GET'])
def show_shell_form():
    return render_template('shell.html')
@app.route("/shell", methods=['POST'])
def execute_command():
    command = request.form['command']
    result = subprocess.run(command.split(), capture_output=True, text=True)
    return str(result.stdout)

@app.route("/open_file", methods=['GET'])
def show_open_file_form():
    return render_template('open_file.html')

@app.route("/open_file", methods=['POST'])
def open_file():
    filepath = request.form['filepath']
    file = open(filepath, 'r', encoding='utf-8')
    return file.read()

@app.route("/request", methods=['GET'])
def show_request_page():
    return render_template('request.html')

@app.route("/request", methods=['POST'])
def make_request():
    url = request.form['url']
    res = requests.get(url)
    return str(res)

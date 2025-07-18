import os
dont_add_middleware = os.getenv("DONT_ADD_MIDDLEWARE")
import aikido_zen # Aikido package import
aikido_zen.protect()

# Sentry :
import sentry_sdk
sentry_sdk.init(
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

import subprocess
from flask import Flask, render_template, request
from flaskext.mysql import MySQL
import requests
import subprocess

app = Flask(__name__)
if dont_add_middleware is None or dont_add_middleware.lower() != "1":
    # Use DONT_ADD_MIDDLEWARE so we don't add this middleware during e.g. benchmarks.
    import aikido_zen
    from aikido_zen.middleware import AikidoFlaskMiddleware
    class SetUserMiddleware:
        def __init__(self, app):
            self.app = app
        def __call__(self, environ, start_response):
            aikido_zen.set_user({"id": "123", "name": "John Doe"})
            return self.app(environ, start_response)
    app.wsgi_app = AikidoFlaskMiddleware(app.wsgi_app)
    app.wsgi_app = SetUserMiddleware(app.wsgi_app)

mysql = MySQL()
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
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

@app.route("/create/via_query", methods=['GET'])
def create_dog_via_query_param():
    dog_name = request.args.get('dog_name')
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
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
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

@app.route("/shell/<string:command>", methods=['GET'])
def execute_command_get(command):
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return str(result.stdout)

# End2End Test route :
@app.route("/test_ratelimiting_1", methods=["GET"])
def test_ratelimiting_1():
    return "OK"

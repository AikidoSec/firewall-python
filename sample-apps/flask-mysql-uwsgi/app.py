from dotenv import load_dotenv
import os
load_dotenv()
firewall_disabled = os.getenv("FIREWALL_DISABLED")
if firewall_disabled is not None:
    if firewall_disabled.lower() != "1":
        import aikido_zen # Aikido package import
        aikido_zen.protect()

from flask import Flask, render_template, request
from flaskext.mysql import MySQL
from werkzeug.wrappers import Request, Response, ResponseStream
from aikido_zen import set_user, should_block_request
from aikido_zen.middleware.flask import AikidoMiddleware
class SimpleMiddleware():
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        print("SimpleMiddleware called")
        return self.app(environ, start_response)
class SetUserMiddleware():
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        set_user({"id": "userid1234", "name": "User"})
        return self.app(environ, start_response)

app = Flask(__name__)
app.wsgi_app = AikidoMiddleware(app.wsgi_app)
app.wsgi_app = SimpleMiddleware(app.wsgi_app)
app.wsgi_app = SimpleMiddleware(app.wsgi_app)
app.wsgi_app = SetUserMiddleware(app.wsgi_app)
app.wsgi_app = SimpleMiddleware(app.wsgi_app)


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

@app.route("/create", methods=['POST'])
def create_dog():
    dog_name = request.form['dog_name']
    connection = mysql.get_db()
    cursor = connection.cursor()
    cursor.execute(f'INSERT INTO dogs (dog_name, isAdmin) VALUES ("%s", 0)' % (dog_name))
    connection.commit()
    return f'Dog {dog_name} created successfully'

from flask import Flask, render_template
from flaskext.mysql import MySQL

app = Flask(__name__)
mysql = MySQL()

app.config['MYSQL_DATABASE_HOST'] = 'db'
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
    cursor.execute("SELECT * FROM db.dogs")
    dog = cursor.fetchmany(1)[0]
    return render_template('dogpage.html', title=f'Dog', dog=dog)

@app.route('/create/<dog_name>')
def create_dog(dog_name):
    connection = mysql.get_db()
    cursor = connection.cursor()
    cursor.execute(''' INSERT INTO dogs (dog_name) VALUES(%s)''',(dog_name))
    connection.commit()
    return f'Dog {(dog_name)}'
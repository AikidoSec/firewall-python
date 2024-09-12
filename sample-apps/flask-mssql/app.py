import os
firewall_disabled = os.getenv("FIREWALL_DISABLED")
if firewall_disabled is not None:
    if firewall_disabled.lower() != "1":
        import aikido_zen # Aikido package import
        aikido_zen.protect()

from flask import Flask, render_template, request
import pymssql

app = Flask(__name__)

# Database configuration
DB_HOST = 'host.docker.internal'
DB_USER = 'sa'
DB_PASSWORD = 'Strong!Passw0rd'
DB_NAME = 'db'

@app.route("/")
def homepage():
    connection = pymssql.connect(server=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM dogs")
    dogs = cursor.fetchall()
    connection.close()
    return render_template('index.html', title='Homepage', dogs=dogs)

@app.route('/dogpage/<int:dog_id>')
def get_dogpage(dog_id):
    connection = pymssql.connect(server=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM dogs WHERE id = %d", (dog_id,))
    dog = cursor.fetchone()
    connection.close()
    if dog:
        return render_template('dogpage.html', title='Dog', dog=dog, isAdmin=("Yes" if dog[2] else "No"))
    else:
        return "Dog not found", 404

@app.route("/create", methods=['GET'])
def show_create_dog_form():
    return render_template('create_dog.html')

@app.route("/create", methods=['POST'])
def create_dog():
    dog_name = request.form['dog_name']
    connection = pymssql.connect(server=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', 0)" % (dog_name))
    connection.commit()
    connection.close()
    return f'Dog {dog_name} created successfully'

if __name__ == '__main__':
    app.run()


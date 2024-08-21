from dotenv import load_dotenv
import os
load_dotenv()
firewall_disabled = os.getenv("FIREWALL_DISABLED")
if firewall_disabled is not None:
    if firewall_disabled.lower() != "1":
        import aikido_firewall # Aikido package import
        aikido_firewall.protect()

from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)
if __name__ == '__main__':
    app.run(threaded=True) # Run threaded so we can test how our bg process works

def get_db_connection():
    return psycopg2.connect(
        host="db",
        database="db",
        user="user",
        password="password")

@app.route("/")
def homepage():
    cursor = get_db_connection().cursor()
    cursor.execute("SELECT * FROM dogs")
    dogs = cursor.fetchall()
    return render_template('index.html', title='Homepage', dogs=dogs)


@app.route('/dogpage/<int:dog_id>')
def get_dogpage(dog_id):
    cursor = get_db_connection().cursor()
    cursor.execute("SELECT * FROM dogs WHERE id = " + str(dog_id))
    dog = cursor.fetchmany(1)[0]
    return render_template('dogpage.html', title=f'Dog', dog=dog, isAdmin=("Yes" if dog[2] else "No"))

@app.route("/upload_xml", methods=['GET'])
def show_upload_xml():
    return render_template('upload_xml.html')



@app.route("/upload_xml", methods=['POST'])
def post_upload_xml():
    #dog_name = request.form['dog_name']
    dog_name = ""

    conn = get_db_connection()
    cursor =  conn.cursor()
    cursor.execute(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % (dog_name))
    conn.commit()
    cursor.close()
    conn.close()
    return f'Dog {dog_name} created successfully'

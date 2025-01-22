import os
import aikido_zen # Aikido package import
aikido_zen.protect()

from flask import Flask, render_template, request
import psycopg2
import xml.etree.ElementTree as ET
import lxml.etree as ET2

app = Flask(__name__)
if __name__ == '__main__':
    app.run(threaded=True) # Run threaded so we can test how our bg process works

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
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

@app.route("/xml", methods=['GET'])
def show_upload_xml():
    return render_template('xml.html')



@app.route("/xml_body", methods=['POST'])
def post_upload_xml():
    raw_xml = request.form['raw_xml']
    root = ET.fromstring(raw_xml)
    conn = get_db_connection()
    cursor =  conn.cursor()
    for dog in root.findall('dog'):
        dog_name = dog.get('dog_name')
        cursor.execute(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % (dog_name))
        conn.commit()
    cursor.close()
    conn.close()
    return f'Dogs created successfully'

@app.route("/xml_post", methods=['POST'])
def post_xml():
    raw_xml = request.data.decode('utf-8')
    root = ET.fromstring(raw_xml)
    ET2.fromstring(raw_xml)
    conn = get_db_connection()
    cursor =  conn.cursor()
    for dog in root.findall('dog'):
        dog_name = dog.get('dog_name')
        cursor.execute(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % (dog_name))
        conn.commit()
    cursor.close()
    conn.close()
    return f'Dogs created successfully'

@app.route("/xml_post_lxml", methods=['POST'])
def post_xml_lxml():
    raw_xml = request.data.decode('utf-8')
    root = ET2.fromstring(raw_xml)
    conn = get_db_connection()
    cursor =  conn.cursor()
    for dog in root.findall('dog'):
        dog_name = dog.get('dog_name')
        cursor.execute(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % (dog_name))
        conn.commit()
    cursor.close()
    conn.close()
    return f'Dogs created successfully'

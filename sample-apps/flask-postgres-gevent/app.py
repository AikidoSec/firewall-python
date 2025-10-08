from gevent import monkey
monkey.patch_all()

import os
import json

import aikido_zen # Aikido package import
aikido_zen.protect()

from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

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

@app.route("/create", methods=['GET'])
def show_create_dog_form():
    return render_template('create_dog.html')

@app.route("/create_many", methods=['GET'])
def show_create_dog_form_many():
    return render_template('create_dog.html')

@app.route("/create", methods=['POST'])
def create_dog():
    dog_name = request.form['dog_name']
    conn = get_db_connection()
    cursor =  conn.cursor()
    cursor.execute(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % (dog_name))
    conn.commit()
    cursor.close()
    conn.close()
    return f'Dog {dog_name} created successfully'

@app.route("/create/:id", methods=["GET"])
@app.route("/create_many", methods=['POST'])
def create_dog_many():
    dog_name = request.form['dog_name']
    conn = get_db_connection()
    cursor =  conn.cursor()
    cursor.executemany([f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % (dog_name)], [])
    conn.commit()
    cursor.close()
    conn.close()
    return f'Dog {dog_name} created successfully'

@app.route("/create_with_cookie", methods=['GET'])
def create_dog_with_cookie():
    dog_name = request.cookies.get('dog_name')

    conn = get_db_connection()
    cursor =  conn.cursor()
    cursor.execute(f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % (dog_name))
    conn.commit()
    cursor.close()
    conn.close()
    return f'Dog {dog_name} created successfully'

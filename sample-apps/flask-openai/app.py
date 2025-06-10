import aikido_zen # Aikido package import
aikido_zen.protect()

import os
from flask import Flask, render_template, request
import psycopg2
import openai
from pydantic import BaseModel

app = Flask(__name__)
client = openai.OpenAI()

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

# OpenAI

@app.route("/openai/<string:subroute>", methods=['GET'])
def show_ask_openai_form(subroute):
    return render_template('ask_openai.html')

@app.route("/openai/responses_create", methods=['POST'])
def openai_responses_create():
    question = request.form['question']

    response = client.responses.create(
        model="gpt-4.1",
        input=question
    )
    answer = response.output_text

    return render_template('ask_openai.html', question=question, answer=answer)

@app.route("/openai/responses_parse", methods=['POST'])
def openai_responses_parse():
    question = request.form['question']

    class CalendarEvent(BaseModel):
        name: str
        date: str
        participants: list[str]
    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {"role": "system", "content": "Extract the event information."},
            {
                "role": "user",
                "content": question,
            },
        ],
        text_format=CalendarEvent,
    )
    answer = f"{response.output_parsed.name} - On {response.output_parsed.date} | People: {response.output_parsed.participants}"

    return render_template('ask_openai.html', question=question, answer=answer)

@app.route("/openai/chat_completions_create", methods=['POST'])
def ask_openai_completions():
    question = request.form['question']

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "Talk like a pirate."},
            {
                "role": "user",
                "content": question,
            },
        ],
    )
    answer = completion.choices[0].message.content

    return render_template('ask_openai.html', question=question, answer=answer)

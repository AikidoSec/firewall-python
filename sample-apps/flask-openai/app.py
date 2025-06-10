import aikido_zen # Aikido package import
aikido_zen.protect()

from flask import Flask, render_template, request
import openai
from pydantic import BaseModel

app = Flask(__name__)
client = openai.OpenAI()

@app.route("/")
def homepage():
    return render_template('index.html', title='Homepage')

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

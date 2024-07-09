from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def homepage():
    dogs = [
        {'id': 1, 'dog_name': 'Buddy'},
        {'id': 2, 'dog_name': 'Max'},
        {'id': 3, 'dog_name': 'Charlie'}
    ]
    return render_template('index.html', title='Homepage', dogs=dogs)


@app.route('/dogpage/<int:dog_id>')
def get_dogpage(dog_id):
    dog = {'id': 3, 'dog_name': 'Charlie'}
    return render_template('dogpage.html', title=f'Dog | {dog["dog_name"]}', dog=dog)

@app.route('/create/<dog_name>')
def create_dog(dog_name):
    return f'Dog {escape(dog_name)}'
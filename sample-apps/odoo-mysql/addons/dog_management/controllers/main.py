import subprocess
import requests
import MySQLdb
from odoo import http
from odoo.http import request


# MySQL connection helper
def get_db_connection():
    return MySQLdb.connect(
        host='mysql',
        user='user',
        password='password',
        database='db'
    )


class DogController(http.Controller):

    @http.route('/', type='http', auth='none', methods=['GET'], csrf=False)
    def homepage(self, **kwargs):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dogs")
            dogs = cursor.fetchall()
            cursor.close()
            conn.close()

            html = '''
            <!DOCTYPE html>
            <html>
            <head><title>Homepage</title></head>
            <body>
                <h1>Dogs List</h1>
                <ul>
            '''
            for dog in dogs:
                html += f'<li><a href="/dogpage/{dog[0]}">{dog[1]}</a></li>'
            html += '''
                </ul>
                <a href="/create">Create a new dog</a>
            </body>
            </html>
            '''
            return request.make_response(html, headers=[('Content-Type', 'text/html')])
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', headers=[('Content-Type', 'text/html')], status=500)

    @http.route('/dogpage/<int:dog_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_dogpage(self, dog_id, **kwargs):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dogs WHERE id = " + str(dog_id))
            dog = cursor.fetchone()
            cursor.close()
            conn.close()

            if dog:
                html = f'''
                <!DOCTYPE html>
                <html>
                <head><title>Dog Page</title></head>
                <body>
                    <h1>{dog[1]}</h1>
                    <p>ID: {dog[0]}</p>
                    <p>Is Admin: {"Yes" if dog[2] else "No"}</p>
                    <a href="/">Back to homepage</a>
                </body>
                </html>
                '''
                return request.make_response(html, headers=[('Content-Type', 'text/html')])
            else:
                return request.make_response('Dog not found', headers=[('Content-Type', 'text/html')], status=404)
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', headers=[('Content-Type', 'text/html')], status=500)

    @http.route('/create', type='http', auth='none', methods=['GET'], csrf=False)
    def show_create_dog_form(self, **kwargs):
        html = '''
        <!DOCTYPE html>
        <html>
        <head><title>Create Dog</title></head>
        <body>
            <h1>Create a new dog</h1>
            <form method="POST" action="/create">
                <label>Dog name:</label>
                <input type="text" name="dog_name" required />
                <button type="submit">Create</button>
            </form>
            <a href="/">Back to homepage</a>
        </body>
        </html>
        '''
        return request.make_response(html, headers=[('Content-Type', 'text/html')])

    @http.route('/create', type='http', auth='none', methods=['POST'], csrf=False)
    def create_dog(self, **kwargs):
        dog_name = request.params.get('dog_name', '')
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f'INSERT INTO dogs (dog_name, isAdmin) VALUES ("{dog_name}", 0)')
            conn.commit()
            cursor.close()
            conn.close()
            return request.make_response(f'Dog {dog_name} created successfully', headers=[('Content-Type', 'text/html')])
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', headers=[('Content-Type', 'text/html')], status=500)

    @http.route('/create/via_query', type='http', auth='none', methods=['GET'], csrf=False)
    def create_dog_via_query_param(self, dog_name=None, **kwargs):
        if not dog_name:
            return request.make_response('Missing dog_name parameter', headers=[('Content-Type', 'text/html')], status=400)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f'INSERT INTO dogs (dog_name, isAdmin) VALUES ("{dog_name}", 0)')
            conn.commit()
            cursor.close()
            conn.close()
            return request.make_response(f'Dog {dog_name} created successfully', headers=[('Content-Type', 'text/html')])
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', headers=[('Content-Type', 'text/html')], status=500)

    @http.route('/multiple_queries', type='http', auth='none', methods=['POST'], csrf=False)
    def multiple_queries(self, **kwargs):
        dog_name = request.params.get('dog_name', '')
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for i in range(20):
                cursor.execute(f'SELECT * FROM dogs WHERE dog_name = "{dog_name}"')
                cursor.fetchmany(1)
            cursor.close()
            conn.close()
            return request.make_response('OK', headers=[('Content-Type', 'text/html')])
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', headers=[('Content-Type', 'text/html')], status=500)

    @http.route('/shell', type='http', auth='none', methods=['GET'], csrf=False)
    def show_shell_form(self, **kwargs):
        html = '''
        <!DOCTYPE html>
        <html>
        <head><title>Shell Command</title></head>
        <body>
            <h1>Execute Shell Command</h1>
            <form method="POST" action="/shell">
                <label>Command:</label>
                <input type="text" name="command" required />
                <button type="submit">Execute</button>
            </form>
            <a href="/">Back to homepage</a>
        </body>
        </html>
        '''
        return request.make_response(html, headers=[('Content-Type', 'text/html')])

    @http.route('/shell', type='http', auth='none', methods=['POST'], csrf=False)
    def execute_command(self, **kwargs):
        command = request.params.get('command', '')
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return request.make_response(str(result.stdout), headers=[('Content-Type', 'text/html')])

    @http.route('/shell/<path:command>', type='http', auth='none', methods=['GET'], csrf=False)
    def execute_command_get(self, command, **kwargs):
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return request.make_response(str(result.stdout), headers=[('Content-Type', 'text/html')])

    @http.route('/open_file', type='http', auth='none', methods=['GET'], csrf=False)
    def show_open_file_form(self, **kwargs):
        html = '''
        <!DOCTYPE html>
        <html>
        <head><title>Open File</title></head>
        <body>
            <h1>Open File</h1>
            <form method="POST" action="/open_file">
                <label>File path:</label>
                <input type="text" name="filepath" required />
                <button type="submit">Open</button>
            </form>
            <a href="/">Back to homepage</a>
        </body>
        </html>
        '''
        return request.make_response(html, headers=[('Content-Type', 'text/html')])

    @http.route('/open_file', type='http', auth='none', methods=['POST'], csrf=False)
    def open_file(self, **kwargs):
        filepath = request.params.get('filepath', '')
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            return request.make_response(content, headers=[('Content-Type', 'text/html')])
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', headers=[('Content-Type', 'text/html')], status=500)

    @http.route('/request', type='http', auth='none', methods=['GET'], csrf=False)
    def show_request_page(self, **kwargs):
        html = '''
        <!DOCTYPE html>
        <html>
        <head><title>Make Request</title></head>
        <body>
            <h1>Make HTTP Request</h1>
            <form method="POST" action="/request">
                <label>URL:</label>
                <input type="text" name="url" required />
                <button type="submit">Send</button>
            </form>
            <a href="/">Back to homepage</a>
        </body>
        </html>
        '''
        return request.make_response(html, headers=[('Content-Type', 'text/html')])

    @http.route('/request', type='http', auth='none', methods=['POST'], csrf=False)
    def make_request(self, **kwargs):
        url = request.params.get('url', '')
        try:
            res = requests.get(url)
            return request.make_response(str(res), headers=[('Content-Type', 'text/html')])
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', headers=[('Content-Type', 'text/html')], status=500)

    @http.route('/test_ratelimiting_1', type='http', auth='none', methods=['GET'], csrf=False)
    def test_ratelimiting_1(self, **kwargs):
        return request.make_response('OK', headers=[('Content-Type', 'text/html')])

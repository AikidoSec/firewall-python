import os
dont_add_middleware = os.getenv("DONT_ADD_MIDDLEWARE")
import aikido_zen  # Aikido package import
aikido_zen.protect()

# Sentry :
import sentry_sdk
sentry_sdk.init(
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

import subprocess
import requests
import MySQLdb
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound


# MySQL connection helper
def get_db_connection():
    return MySQLdb.connect(
        host='localhost',
        user='user',
        password='password',
        database='db'
    )


class OdooStyleWSGIApp:
    """
    A WSGI application inspired by Odoo's routing pattern.
    Uses Werkzeug for routing and request/response handling.
    """

    def __init__(self):
        self.url_map = Map([
            Rule('/', endpoint='homepage', methods=['GET']),
            Rule('/dogpage/<int:dog_id>', endpoint='get_dogpage', methods=['GET']),
            Rule('/create', endpoint='show_create_dog_form', methods=['GET']),
            Rule('/create', endpoint='create_dog', methods=['POST']),
            Rule('/create/via_query', endpoint='create_dog_via_query_param', methods=['GET']),
            Rule('/multiple_queries', endpoint='multiple_queries', methods=['POST']),
            Rule('/shell', endpoint='show_shell_form', methods=['GET']),
            Rule('/shell', endpoint='execute_command', methods=['POST']),
            Rule('/shell/<path:command>', endpoint='execute_command_get', methods=['GET']),
            Rule('/open_file', endpoint='show_open_file_form', methods=['GET']),
            Rule('/open_file', endpoint='open_file', methods=['POST']),
            Rule('/request', endpoint='show_request_page', methods=['GET']),
            Rule('/request', endpoint='make_request', methods=['POST']),
            Rule('/test_ratelimiting_1', endpoint='test_ratelimiting_1', methods=['GET']),
        ])

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, endpoint)(request, **values)
        except NotFound:
            return Response('Not Found', status=404)
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    # Route handlers (mimicking Odoo's controller methods)

    def homepage(self, request):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM db.dogs")
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
            return Response(html, content_type='text/html')
        except Exception as e:
            return Response(f'Error: {str(e)}', content_type='text/html', status=500)

    def get_dogpage(self, request, dog_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM db.dogs WHERE id = " + str(dog_id))
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
                return Response(html, content_type='text/html')
            else:
                return Response('Dog not found', content_type='text/html', status=404)
        except Exception as e:
            return Response(f'Error: {str(e)}', content_type='text/html', status=500)

    def show_create_dog_form(self, request):
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
        return Response(html, content_type='text/html')

    def create_dog(self, request):
        dog_name = request.form.get('dog_name', '')
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f'INSERT INTO dogs (dog_name, isAdmin) VALUES ("{dog_name}", 0)')
            conn.commit()
            cursor.close()
            conn.close()
            return Response(f'Dog {dog_name} created successfully', content_type='text/html')
        except Exception as e:
            return Response(f'Error: {str(e)}', content_type='text/html', status=500)

    def create_dog_via_query_param(self, request):
        dog_name = request.args.get('dog_name', '')
        if not dog_name:
            return Response('Missing dog_name parameter', content_type='text/html', status=400)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f'INSERT INTO dogs (dog_name, isAdmin) VALUES ("{dog_name}", 0)')
            conn.commit()
            cursor.close()
            conn.close()
            return Response(f'Dog {dog_name} created successfully', content_type='text/html')
        except Exception as e:
            return Response(f'Error: {str(e)}', content_type='text/html', status=500)

    def multiple_queries(self, request):
        dog_name = request.form.get('dog_name', '')
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for i in range(20):
                cursor.execute(f'SELECT * FROM db.dogs WHERE dog_name = "{dog_name}"')
                cursor.fetchmany(1)
            cursor.close()
            conn.close()
            return Response('OK', content_type='text/html')
        except Exception as e:
            return Response(f'Error: {str(e)}', content_type='text/html', status=500)

    def show_shell_form(self, request):
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
        return Response(html, content_type='text/html')

    def execute_command(self, request):
        command = request.form.get('command', '')
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return Response(str(result.stdout), content_type='text/html')

    def execute_command_get(self, request, command):
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return Response(str(result.stdout), content_type='text/html')

    def show_open_file_form(self, request):
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
        return Response(html, content_type='text/html')

    def open_file(self, request):
        filepath = request.form.get('filepath', '')
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            return Response(content, content_type='text/html')
        except Exception as e:
            return Response(f'Error: {str(e)}', content_type='text/html', status=500)

    def show_request_page(self, request):
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
        return Response(html, content_type='text/html')

    def make_request(self, request):
        url = request.form.get('url', '')
        try:
            res = requests.get(url)
            return Response(str(res), content_type='text/html')
        except Exception as e:
            return Response(f'Error: {str(e)}', content_type='text/html', status=500)

    def test_ratelimiting_1(self, request):
        return Response('OK', content_type='text/html')


# Create the WSGI application
app = OdooStyleWSGIApp()


# WSGI application wrapper with Aikido middleware
def application(environ, start_response):
    # Apply Aikido middleware if enabled
    if dont_add_middleware is None or dont_add_middleware.lower() != "1":
        import aikido_zen
        from aikido_zen.middleware import AikidoWSGIMiddleware

        # Set user for Aikido
        aikido_zen.set_user({"id": "123", "name": "John Doe"})

        # Wrap WSGI application with Aikido middleware
        wrapped_app = AikidoWSGIMiddleware(app)
        return wrapped_app(environ, start_response)

    return app(environ, start_response)


if __name__ == '__main__':
    # For development/testing
    from werkzeug.serving import run_simple
    port = int(os.getenv('PORT', 8114))
    run_simple('0.0.0.0', port, application, use_debugger=False, use_reloader=False)

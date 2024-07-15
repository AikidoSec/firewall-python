import importhook
from flask import Flask
def install_flask_middleware(app):
    def flask_middleware(environ, start_response):
        print("Flask middleware ran")
        return app(environ, start_response)
    app.wsgi_app = flask_middleware

def aikido_flask_init(_self, *args, **kwargs):
        super(Flask, _self).__init__(*args, **kwargs)
        # Insert here (e.g.)
        @_self.route("/aikido")
        def homepage2():
            return "Aikido link"
        # End insert

@importhook.on_import('flask')
def on_flask_import(flask):
    modified_flask = importhook.copy_module(flask)
    setattr(modified_flask.Flask, "__init__", aikido_flask_init)
    print("Modified flask")
    return modified_flask
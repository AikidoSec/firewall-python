import importhook

def generate_flask_middleware(app):
    def flask_middleware(environ, start_response):
        print("Flask middleware ran")
        return app(environ, start_response)
    return flask_middleware


@importhook.on_import('flask')
def on_django_import(flask):
    modified_flask = importhook.copy_module(flask)
    setattr(modified_flask.Flask, "__init__", generate_flask_init(flask))
    print("Modified flask")
    return modified_flask
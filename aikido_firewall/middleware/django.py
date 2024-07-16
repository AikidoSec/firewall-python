class AikidoMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        print("[AIK] Aikido middleware is working")
        response = self.app(environ, start_response)
        return response
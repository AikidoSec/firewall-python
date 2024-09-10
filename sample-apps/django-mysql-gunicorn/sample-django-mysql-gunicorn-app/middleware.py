
from aikido_zen import set_user
class SimpleAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        print("Setting user")
        set_user({
            "id": 100,
            "name": "test user"
        })
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response

import logging
class AikidoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        logging.critical("[AIK] Aikido middleware : call")
        return self.get_response(request)

    def process_exception(self, request, exception):
        logging.critical("[AIK] Aikido middleware : exception")
    
    def process_request(self, request):
        logging.critical("[AIK] Aikido middleware : request")

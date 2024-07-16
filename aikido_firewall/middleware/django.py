import logging
class AikidoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        logging.info("[AIK] Aikido middleware : call")
        return self.get_response(request)

    def process_exception(self, request, exception):
        logging.info("[AIK] Aikido middleware : exception")
    
    def process_request(self, request):
        logging.info("[AIK] Aikido middleware : request")

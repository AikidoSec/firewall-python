import requests

class Request:
    def __init__(self, route, method='POST', headers=None, data_type='json', body=None, cookies={}):
        self.method = method
        self.route = route
        self.headers = headers if headers is not None else {}
        self.data_type = data_type  # 'json' or 'form'
        self.body = body
        self.cookies = cookies

    def execute(self, base_url):
        """Execute the request and return the status code."""
        url = f"{base_url}{self.route}"

        if self.method.upper() == 'POST':
            if self.data_type == 'json':
                response = requests.post(url, json=self.body, headers=self.headers, cookies=self.cookies)
            elif self.data_type == 'form':
                response = requests.post(url, data=self.body, headers=self.headers, cookies=self.cookies)
            else:
                raise ValueError("Unsupported data type. Use 'json' or 'form'.")
        elif self.method.upper() == 'GET':
            response = requests.get(url, headers=self.headers, cookies=self.cookies)
        else:
            raise ValueError("Unsupported HTTP method. Use 'GET' or 'POST'.")

        return response.status_code
    def __str__(self):
        return f"Request(method={self.method}, route={self.route}, headers={self.headers}, data_type={self.data_type}, body={self.body})"

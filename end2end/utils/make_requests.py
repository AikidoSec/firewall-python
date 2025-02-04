import urllib.parse

import requests


# Function to make a POST request
def make_post_request(url, data, status_code, user_id=None, json=True):
    headers = {}
    response = None
    if user_id is not None:
        headers['user'] = user_id
    if json is True:
        response = requests.post(url, json=data, headers=headers)
    else:
        response = requests.post(url, data=data, headers=headers)

    # Assert that the status code is 200
    assert response.status_code == status_code, f"Expected status code {status_code} but got {response.status_code}"


def make_path_var_request(url, variable, status_code):
    response = requests.get(url + urllib.parse.quote(variable))

    # Assert that the status code is 200
    assert response.status_code == status_code, f"Expected status code {status_code} but got {response.status_code}"

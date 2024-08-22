import pytest
import requests
# e2e tests for flask_mysql sample app
post_url_fw = "http://localhost:8086/create"
post_url_nofw = "http://localhost:8087/create"

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 500

def test_dangerous_response_without_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200


import pytest
import requests
# e2e tests for flask_postgres sample app
post_url_fw = "http://localhost:8092/xml_post"
post_url_nofw = "http://localhost:8093/xml_post"

def test_safe_response_with_firewall():
    xml_data = '<dogs><dog dog_name="Bobby" /></dogs>'
    res = requests.post(post_url_fw, data=xml_data)
    assert res.status_code == 200


def test_safe_response_without_firewall():
    xml_data = '<dogs><dog dog_name="Bobby" /></dogs>'
    res = requests.post(post_url_nofw, data=xml_data)
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    xml_data = '<dogs><dog dog_name="Malicious dog\', TRUE); -- " /></dogs>'
    res = requests.post(post_url_fw, data=xml_data)
    assert res.status_code == 500

def test_dangerous_response_without_firewall():
    xml_data = '<dogs><dog dog_name="Malicious dog\', TRUE); -- " /></dogs>'
    res = requests.post(post_url_nofw, data=xml_data)
    assert res.status_code == 200


import requests
from utils.assert_equals import assert_eq

def test_ip_blocking(url):
    # Allowed IP :
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.1"
    })
    assert_eq(res.status_code, equals=200)

    # Blocked IP :
    res = requests.get(url, headers={
        'X-Forwarded-For': "1.2.3.4"
    })
    assert_eq(res.status_code, equals=403)
    assert_eq(res.text, equals="Your IP address is blocked due to geo restrictions (Your IP: 1.2.3.4)")

    # More complex X-Forwarded-For :
    res = requests.get(url, headers={
        'X-Forwarded-For': "invalid.ip.here.now, 1.2.3.4 "
    })
    assert_eq(res.status_code, equals=403)
    assert_eq(res.text, equals="Your IP address is blocked due to geo restrictions (Your IP: 1.2.3.4)")

    # More complex but safe X-Forwarded-For :
    res = requests.get(url, headers={
        'X-Forwarded-For': "invalid.ip.here.now, 192.168.1.1 "
    })
    assert_eq(res.status_code, equals=200)

    # It should only use the first valid ip
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.1, 1.2.3.4"
    })
    assert_eq(res.status_code, equals=200)

    # It should work with an empty X-Forwarded-For
    res = requests.get(url, headers={
        'X-Forwarded-For': ""
    })
    assert_eq(res.status_code, equals=200)

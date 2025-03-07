import time
import requests
from utils.assert_equals import assert_eq

def test_ratelimiting(url):
    # Test route (First req & 2nd Req) :
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.1"
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.1"
    })
    assert_eq(res.status_code, equals=200)

    # 3rd & 4th (blocked) requests :
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.1"
    })
    assert_eq(res.status_code, equals=429)
    assert_eq(res.text, equals="You are rate limited by Zen. (Your IP: 192.168.1.1)")
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.1"
    })
    assert_eq(res.status_code, equals=429)
    assert_eq(res.text, equals="You are rate limited by Zen. (Your IP: 192.168.1.1)")

    # Now do the same but with a different IP in the same time block :
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2"
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2"
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2"
    })
    assert_eq(res.status_code, equals=429)
    assert_eq(res.text, equals="You are rate limited by Zen. (Your IP: 192.168.1.2)")
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2"
    })
    assert_eq(res.status_code, equals=429)
    assert_eq(res.text, equals="You are rate limited by Zen. (Your IP: 192.168.1.2)")

    # Now wait 5 seconds so your window is over and re-request :
    time.sleep(5)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2"
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.1"
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2"
    })
    assert_eq(res.status_code, equals=200)
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.1"
    })
    assert_eq(res.status_code, equals=200)


def test_ratelimiting_per_user(url):
    # Test route (First req & 2nd Req) :
    res = requests.get(url, headers={
        'user': 'id1'
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'user': 'id1'
    })
    assert_eq(res.status_code, equals=200)

    # 3rd & 4th (blocked) requests :
    res = requests.get(url, headers={
        'user': 'id1'
    })
    assert_eq(res.status_code, equals=429)
    assert_eq(res.text, equals="You are rate limited by Zen.")
    res = requests.get(url, headers={
        'user': 'id1'
    })
    assert_eq(res.status_code, equals=429)
    assert_eq(res.text, equals="You are rate limited by Zen.")

    # Now do the same but with a different User in the same time block :
    res = requests.get(url, headers={
        'user': 'id2'
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'user': 'id2'
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'user': 'id2'
    })
    assert_eq(res.status_code, equals=429)
    assert_eq(res.text, equals="You are rate limited by Zen.")
    res = requests.get(url, headers={
        'user': 'id2'
    })
    assert_eq(res.status_code, equals=429)
    assert_eq(res.text, equals="You are rate limited by Zen.")

    # Now wait 5 seconds so your window is over and re-request :
    time.sleep(5)
    res = requests.get(url, headers={
        'user': 'id2'
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'user': 'id1'
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'user': 'id2'
    })
    assert_eq(res.status_code, equals=200)
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'user': 'id1'
    })
    assert_eq(res.status_code, equals=200)

    # Test it prefers user over IP :
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2"
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2"
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2",
        'user': 'id3'
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2",
        'user': 'id4'
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2",
        'user': 'id5'
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'X-Forwarded-For': "192.168.1.2",
        'user': 'id6'
    })
    assert_eq(res.status_code, equals=200)
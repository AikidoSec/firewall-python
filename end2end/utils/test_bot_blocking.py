import requests
from utils.assert_equals import assert_eq

def test_bot_blocking(url):
    # Allowed User-Agents :
    res = requests.get(url, headers={
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    })
    assert_eq(res.status_code, equals=200)
    res = requests.get(url, headers={
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.0 Chrome/91.0.4472.114 Mobile Safari/537.36"
    })
    assert_eq(res.status_code, equals=200)

    # Blocked User-Agent :
    res = requests.get(url, headers={
        'User-Agent': "BYTESPIDER"
    })
    assert_eq(res.status_code, equals=403)
    assert_eq(res.text, equals="You are not allowed to access this resource because you have been identified as a bot.")

    # More complex blocked User-Agent :
    res = requests.get(url, headers={
        'User-Agent': "Mozilla/5.0 (compatible; Bytespider/1.0; +http://bytespider.com/bot.html)"
    })
    assert_eq(res.status_code, equals=403)
    assert_eq(res.text, equals="You are not allowed to access this resource because you have been identified as a bot.")
    res = requests.get(url, headers={
        'User-Agent': "Mozilla/5.0 (compatible; AI2Bot/1.0; +http://www.aaai.org/Press/Reports/AI2Bot)"
    })
    assert_eq(res.status_code, equals=403)
    assert_eq(res.text, equals="You are not allowed to access this resource because you have been identified as a bot.")

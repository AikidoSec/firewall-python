from aikido_zen.vulnerabilities.attack_wave_detection.is_web_scan_method import is_web_scan_method


def test_is_web_scan_method():
    assert is_web_scan_method("BADMETHOD")
    assert is_web_scan_method("BADHTTPMETHOD")
    assert is_web_scan_method("BADDATA")
    assert is_web_scan_method("BADMTHD")
    assert is_web_scan_method("BDMTHD")

def test_is_not_web_scan_method():
    assert not is_web_scan_method("GET")
    assert not is_web_scan_method("POST")
    assert not is_web_scan_method("PUT")
    assert not is_web_scan_method("DELETE")
    assert not is_web_scan_method("PATCH")
    assert not is_web_scan_method("OPTIONS")
    assert not is_web_scan_method("HEAD")
    assert not is_web_scan_method("TRACE")
    assert not is_web_scan_method("CONNECT")
    assert not is_web_scan_method("PURGE")

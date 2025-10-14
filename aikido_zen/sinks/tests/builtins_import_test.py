import os
os.putenv("AIKIDO_DEBUG", "true")
os.putenv("AIKIDO_TOKEN", "test")

import aikido_zen
aikido_zen.protect()
#from aikido_zen.background_process.packages import PackagesStore


#def test_flask_import(monkeypatch):
#    monkeypatch.setenv("AIKIDO_DEBUG", "1")
#    import flask
#    assert PackagesStore.get_package("flask")["version"] == "3.0.3"

def test_recursion():
    import aikido_zen.sinks.tests.test_recursion_module

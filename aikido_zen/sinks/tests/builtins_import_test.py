import os
import sys

os.putenv("AIKIDO_DEBUG", "true")
os.putenv("AIKIDO_TOKEN", "test")

#from aikido_zen.background_process.packages import PackagesStore


#def test_flask_import(monkeypatch):
#    monkeypatch.setenv("AIKIDO_DEBUG", "1")
#    import flask
#    assert PackagesStore.get_package("flask")["version"] == "3.0.3"

def test_recursion():
    import aikido_zen.sinks.builtins_import
    __import__("aikido_zen.sinks.tests.builins_import_recursion_test")
    module = sys.modules["aikido_zen.sinks.tests.builins_import_recursion_test"]

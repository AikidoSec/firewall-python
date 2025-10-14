import zipp
import aikido_zen
aikido_zen.protect()
import aikido_zen.sinks.builtins_import
#from aikido_zen.background_process.packages import PackagesStore


#def test_flask_import(monkeypatch):
#    monkeypatch.setenv("AIKIDO_DEBUG", "1")
#    import flask
#    assert PackagesStore.get_package("flask")["version"] == "3.0.3"

def test_recursion(monkeypatch):
    monkeypatch.setenv("AIKIDO_DEBUG", "1")
    import zipp.compat.overlay

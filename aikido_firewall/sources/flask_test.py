"""
Test file for flask.py
"""

# pylint: disable=unused-import
import pytest
import aikido_firewall.sources.flask as aik_flask


class TestAikidoMiddleware:
    """Test class"""

    def test_aikido_middleware_init(self, mocker):
        """Testing for AikidoMiddleware __init__ function"""
        app = mocker.MagicMock()
        middleware = aik_flask.AikidoMiddleware(app)
        assert middleware.app == app

    def test_aikido_middleware_call(self, mocker):
        """Testing for AikidoMiddleware __call__ function"""
        app = mocker.MagicMock()
        app.return_value = 1
        environ, start_response = (2, 3)
        middleware = aik_flask.AikidoMiddleware(app)

        response = middleware(environ, start_response)
        args, kwargs = app.call_args

        assert args == (environ, start_response)
        assert response == 1

    def test_on_flask_import(self, mocker):
        """Testing for on_flask_import"""
        pass

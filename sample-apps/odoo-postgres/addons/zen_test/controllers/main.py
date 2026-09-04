import subprocess

from odoo import http, release
from odoo.http import Response, request

JSON_ROUTE_TYPE = "jsonrpc" if release.version_info[0] >= 19 else "json"


def _text_response(value, status=200):
    return request.make_response(
        value,
        headers=[("Content-Type", "text/plain; charset=utf-8")],
        status=status,
    )


def _execute_command(command):
    subprocess.run(command, capture_output=True, check=False, shell=True, text=True)
    return command


def _record_side_effect(name):
    request.env["zen.test.side.effect"].sudo().create({"name": name})


class ZenTestController(http.Controller):
    @http.route("/zen/status", type="http", auth="public", methods=["GET"])
    def status(self):
        return _text_response("ok")

    @http.route("/zen/shell/query", type="http", auth="public", methods=["GET"])
    def shell_query(self, command=""):
        return _text_response(_execute_command(command))

    @http.route(
        "/zen/shell/form",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def shell_form(self, command=""):
        return _text_response(_execute_command(command))

    @http.route(
        "/zen/shell/json",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def shell_json(self):
        command = request.get_json_data().get("command", "")
        return _text_response(_execute_command(command))

    @http.route(
        "/zen/shell/jsonrpc",
        type=JSON_ROUTE_TYPE,
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def shell_jsonrpc(self, command=""):
        return _execute_command(command)

    @http.route("/zen/shell/header", type="http", auth="public", methods=["GET"])
    def shell_header(self):
        command = request.httprequest.headers.get("X-Command", "")
        return _text_response(_execute_command(command))

    @http.route("/zen/shell/cookie", type="http", auth="public", methods=["GET"])
    def shell_cookie(self):
        command = request.httprequest.cookies.get("command", "")
        return _text_response(_execute_command(command))

    @http.route(
        "/zen/shell/route/<path:command>",
        type="http",
        auth="public",
        methods=["GET"],
    )
    def shell_route(self, command):
        return _text_response(_execute_command(command))

    @http.route("/zen/sql", type="http", auth="public", methods=["GET"])
    def unsafe_sql(self, query="SELECT 1"):
        request.env.cr.execute(query)
        result = request.env.cr.fetchone() if request.env.cr.description else None
        return _text_response(repr(result))

    @http.route("/zen/error", type="http", auth="public", methods=["GET"])
    def error(self):
        raise RuntimeError("Intentional exception from the Zen Odoo test addon")

    @http.route("/zen/stream", type="http", auth="public", methods=["GET"])
    def stream(self):
        def chunks():
            yield b"first\n"
            yield b"second\n"

        return Response(chunks(), content_type="text/plain")

    @http.route("/zen/user", type="http", auth="user", methods=["GET"])
    def user(self):
        return _text_response(str(request.session.uid))

    @http.route(
        "/zen/request-block-side-effect",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def request_block_side_effect(self):
        _record_side_effect("request-block")
        return _text_response("recorded")

    @http.route(
        "/zen/rate-limit-side-effect",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def rate_limit_side_effect(self):
        _record_side_effect("rate-limit")
        return _text_response("recorded")

    @http.route(
        "/zen/side-effects/<string:name>",
        type="http",
        auth="public",
        methods=["GET"],
    )
    def side_effect_count(self, name):
        count = (
            request.env["zen.test.side.effect"]
            .sudo()
            .search_count([("name", "=", name)])
        )
        return _text_response(str(count))

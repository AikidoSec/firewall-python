import os
import subprocess
import xml.etree.ElementTree as ElementTree

from odoo import http, release
from odoo.http import request

from ..models.dog import INSERT_UNSAFE

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


class ZenTestController(http.Controller):
    @http.route("/zen/status", type="http", auth="public", methods=["GET"])
    def status(self):
        return _text_response("ok")

    @http.route("/zen/shell/query", type="http", auth="public", methods=["GET"])
    def shell_query(self, command=""):
        return _text_response(_execute_command(command))

    @http.route(
        "/zen/shell/form", type="http", auth="public", methods=["POST"], csrf=False
    )
    def shell_form(self, command=""):
        return _text_response(_execute_command(command))

    @http.route("/zen/shell/header", type="http", auth="public", methods=["GET"])
    def shell_header(self):
        command = request.httprequest.headers.get("X-Command", "")
        return _text_response(_execute_command(command))

    @http.route("/zen/shell/cookie", type="http", auth="public", methods=["GET"])
    def shell_cookie(self):
        command = request.httprequest.cookies.get("command", "")
        return _text_response(_execute_command(command))

    @http.route("/zen/files/<string:name>", type="http", auth="public", methods=["GET"])
    def file_exists(self, name):
        return _text_response(
            "yes" if os.path.exists("/tmp/zen_files/" + name) else "no"
        )

    @http.route("/zen/upload", type="http", auth="public", methods=["POST"], csrf=False)
    def upload(self, upload):
        with open("/tmp/zen_files/" + upload.filename, "w") as file:
            file.write("uploaded")
        return _text_response("saved")


class ZenAttackController(http.Controller):
    @http.route("/zen/dog", type=JSON_ROUTE_TYPE, auth="public", csrf=False)
    def dog_jsonrpc(self, dog_name):
        request.env.cr.execute(INSERT_UNSAFE % dog_name)
        return dog_name

    @http.route("/zen/dog_safe", type=JSON_ROUTE_TYPE, auth="public", csrf=False)
    def dog_jsonrpc_safe(self, dog_name):
        request.env.cr.execute(
            "INSERT INTO zen_test_dog (name, is_admin) VALUES (%s, FALSE)",
            (dog_name,),
        )
        return dog_name

    @http.route(
        "/zen/dog/owner/<string:owner>/<string:dog_name>",
        type="http",
        auth="public",
        methods=["GET"],
    )
    def dog_route(self, owner, dog_name):
        request.env.cr.execute(INSERT_UNSAFE % dog_name)
        return _text_response("stored")

    @http.route(
        "/zen/dog/text", type="http", auth="public", methods=["POST"], csrf=False
    )
    def dog_text(self):
        request.env.cr.execute(
            INSERT_UNSAFE % request.httprequest.get_data(as_text=True)
        )
        return _text_response("stored")

    @http.route(
        "/zen/dog/xml", type="http", auth="public", methods=["POST"], csrf=False
    )
    def dog_xml(self):
        root = ElementTree.fromstring(request.httprequest.get_data(as_text=True))
        request.env.cr.execute(INSERT_UNSAFE % root.find("dog").get("name"))
        return _text_response("stored")

    @http.route("/zen/dogs/count", type="http", auth="public", methods=["GET"])
    def dog_count(self, name=None):
        if name is None:
            request.env.cr.execute("SELECT count(*) FROM zen_test_dog WHERE is_admin")
        else:
            request.env.cr.execute(
                "SELECT count(*) FROM zen_test_dog WHERE name = %s", (name,)
            )
        return _text_response(str(request.env.cr.fetchone()[0]))

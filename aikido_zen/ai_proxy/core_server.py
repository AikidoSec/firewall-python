"""
Plays the role of Aikido's cloud from the AI proxy's point of view: serves the
`fetchPermissions`/`fetchAiPermissions` config endpoints it polls, and collects
the events it reports.

Runs as a thread inside the background process. Deliberately holds no cloud
credentials and never talks to Aikido's cloud itself — config comes from the
`ServiceConfig` this same process already has, and every received event is
handed to `event_sink` (the background process's existing event queue), which
reports it onward exactly like a `detected_attack` event.
"""

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from aikido_zen.helpers.logging import logger

# The proxy POSTs to `{reporting_endpoint}/events/<name>` (see
# proxy-lib/src/http/firewall/notifier.rs); the name becomes the reported
# event's `type` as-is.
EVENT_TYPES = ("ai-usage", "ai-tool-hits", "ai-rules-engine-findings")


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class AiCoreServer:
    """config_provider() -> {"ai_enabled", "blocked_ai_tools", "ai_rules"}
    event_sink(event: dict) is called once per reported event, already carrying
    a "type" key."""

    def __init__(self, config_provider, event_sink):
        self.config_provider = config_provider
        self.event_sink = event_sink
        self.port = free_port()
        self._server = HTTPServer(("127.0.0.1", self.port), self._make_handler())
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="zen-ai-core-server", daemon=True
        )

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def start(self):
        self._thread.start()

    def stop(self):
        self._server.shutdown()
        self._server.server_close()

    def _make_handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def _send_json(self, obj, code=200):
                body = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if "fetchAiPermissions" in self.path:
                    config = outer.config_provider()
                    self._send_json({
                        "blocked_ai_tools": config.get("blocked_ai_tools", []),
                        "ai_rules": config.get("ai_rules", []),
                    })
                elif "fetchPermissions" in self.path:
                    config = outer.config_provider()
                    self._send_json({
                        # permission_group is a required field for the proxy to
                        # accept this response at all; its content is unused.
                        "permission_group": {"id": 1, "name": "zen-python-agent"},
                        "ecosystems": {},
                        "custom_registries": [],
                        "feature_flags": {
                            "ai_features_enabled": bool(config.get("ai_enabled", True))
                        },
                    })
                else:
                    self._send_json({"error": "not found"}, 404)

            def do_POST(self):
                event_type = next(
                    (t for t in EVENT_TYPES if self.path.endswith(f"/events/{t}")), None
                )

                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""

                if event_type is None:
                    logger.debug("AI proxy posted to unknown path: %s", self.path)
                    self._send_json({"ok": False}, 404)
                    return

                try:
                    body = json.loads(raw) if raw else {}
                except ValueError:
                    logger.debug("AI proxy sent non-JSON event body on %s", self.path)
                    self._send_json({"ok": False}, 400)
                    return

                try:
                    event = dict(body)
                    event["type"] = event_type
                    outer.event_sink(event)
                except Exception as e:
                    logger.debug("Failed to hand AI proxy event to sink: %s", e)

                self._send_json({"ok": True})

            def log_message(self, *_):
                pass

        return Handler

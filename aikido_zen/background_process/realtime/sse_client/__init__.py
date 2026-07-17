"""
SSE (Server-Sent Events) client that connects to the realtime endpoint and
dispatches events, automatically reconnecting with exponential backoff and
jitter on disconnects.
"""

import http.client
import random
import socket
import threading
import time
import urllib.error
import urllib.request

import aikido_zen.background_process.realtime as realtime
from aikido_zen.helpers.logging import logger
from .parser import SSEParser
import aikido_zen.config as config

INITIAL_RECONNECT_SECS = 5
MAX_RECONNECT_SECS = 60
STABLE_CONNECTION_SECS = 30
READ_TIMEOUT_SECS = 70

_CONNECTION_ERRORS = (urllib.error.URLError, OSError, http.client.HTTPException)


def connect_to_sse(
    token,
    on_event,
    initial_reconnect_secs=INITIAL_RECONNECT_SECS,
    read_timeout_secs=READ_TIMEOUT_SECS,
):
    """
    Starts a daemon thread that connects to the realtime SSE endpoint and calls
    `on_event(event)` for every event received. Reconnects with exponential
    backoff (and jitter) on disconnect, until the server rejects the connection
    with a 401 or 403 status, at which point it stops.

    Returns the thread that was started.
    """
    thread = threading.Thread(
        target=_reconnect_loop,
        args=(token, on_event, initial_reconnect_secs, read_timeout_secs),
        daemon=True,
    )
    thread.start()
    return thread


def _reconnect_loop(token, on_event, initial_reconnect_secs, read_timeout_secs):
    reconnect_secs = initial_reconnect_secs
    while True:
        try:
            start = time.monotonic()
            outcome, status_code = _connect(token, on_event, read_timeout_secs)

            if outcome == "disconnected" and status_code in (401, 403):
                logger.info(
                    "SSE connection rejected with status %s, stopping", status_code
                )
                return

            if time.monotonic() - start >= STABLE_CONNECTION_SECS:
                reconnect_secs = initial_reconnect_secs
        except Exception as e:
            logger.error("SSE loop error : %s", e)

        jitter = random.random() * (reconnect_secs / 2)
        delay_secs = reconnect_secs + jitter

        logger.debug("SSE scheduling reconnect in %sms", round(delay_secs * 1000))

        reconnect_secs = min(reconnect_secs * 2, MAX_RECONNECT_SECS)

        time.sleep(delay_secs)


def _connect(token, on_event, read_timeout_secs):
    """
    Opens a single SSE connection and dispatches events until the connection is
    closed, errors out, or goes idle for longer than `read_timeout_secs`.

    Returns a tuple of (outcome, status_code), where outcome is either "error"
    (the connection could not be made, or timed out) or "disconnected" (a
    response was received, but the connection has since ended).
    """
    url = f"{realtime.get_realtime_url()}api/runtime/stream"
    logger.debug("SSE connecting to %s", url)

    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": str(token),
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "X-Agent-Platform": "python",
            "X-Agent-Version": config.PKG_VERSION,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=read_timeout_secs) as response:
            status_code = response.getcode()
            if status_code != 200:
                return "disconnected", status_code

            logger.debug("SSE connected successfully")

            parser = SSEParser(response)
            try:
                for event in parser.events():
                    logger.debug("SSE received event : %s", event)
                    on_event(event)
            except socket.timeout:
                logger.debug("SSE read timeout")
                return "error", None
            except _CONNECTION_ERRORS as e:
                logger.debug("SSE stream error : %s", e)
                return "disconnected", status_code
            except Exception as e:
                logger.debug("SSE parser or callback error : %s", e)
                return "error", None
    except urllib.error.HTTPError as e:
        logger.debug("SSE connection rejected with status %s", e.code)
        return "disconnected", e.code
    except _CONNECTION_ERRORS as e:
        logger.debug("SSE connection error : %s", e)
        return "error", None

    logger.debug("SSE connection closed by server")
    return "disconnected", status_code

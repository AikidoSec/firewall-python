import importlib
import socket
from multiprocessing import connection
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from aikido_zen.background_process.commands import process_incoming_command
from aikido_zen.background_process.commands.put_event import PutEventReq


def test_event_is_acknowledged_after_enqueueing():
    operations = []
    events = Mock()
    events.put.side_effect = lambda event: operations.append(("queued", event))
    connection = Mock()
    connection.send.side_effect = lambda value: operations.append(("reply", value))
    event = {"name": "login.failed"}

    process_incoming_command(
        None, ("PUT_EVENT", PutEventReq(event)), connection, events
    )

    assert operations == [("queued", event), ("reply", None)]
    connection.send.assert_called_once_with(None)


def test_event_is_not_acknowledged_when_enqueueing_fails():
    events = Mock()
    events.put.side_effect = RuntimeError("Queue unavailable")
    connection = Mock()

    with pytest.raises(RuntimeError, match="Queue unavailable"):
        process_incoming_command(
            None,
            ("PUT_EVENT", PutEventReq({"name": "login.failed"})),
            connection,
            events,
        )

    connection.send.assert_not_called()


@pytest.mark.parametrize("failure", ["receive", "reply", "command"])
def test_receiver_closes_failed_connection_before_accepting_next(monkeypatch, failure):
    background = importlib.import_module(
        "aikido_zen.background_process.aikido_background_process"
    )

    class ListenerFinished(Exception):
        pass

    failed_socket, failed_client_socket = socket.socketpair()
    next_socket, next_client_socket = socket.socketpair()
    failed = connection.Connection(failed_socket.detach())
    failed_client = connection.Connection(failed_client_socket.detach())
    next_peer = connection.Connection(next_socket.detach())
    next_client = connection.Connection(next_client_socket.detach())
    accepted = []

    def accept():
        if accepted:
            assert accepted[-1].closed
        if len(accepted) == 2:
            raise ListenerFinished
        peer = (failed, next_peer)[len(accepted)]
        accepted.append(peer)
        return peer

    monkeypatch.setattr(
        background.con,
        "Listener",
        lambda *args, **kwargs: SimpleNamespace(accept=accept),
    )
    monkeypatch.setattr(
        background,
        "Thread",
        lambda *args, **kwargs: SimpleNamespace(start=lambda: None),
    )
    monkeypatch.setattr(background, "add_exit_handlers", lambda: None)
    monkeypatch.setattr(background, "set_agent_session_id", lambda value: None)
    try:
        if failure != "receive":
            failed_client.send(None if failure == "command" else ("PING", ()))
        failed_client.close()
        next_client.send(("PING", ()))

        with pytest.raises(ListenerFinished):
            background.AikidoBackgroundProcess(("127.0.0.1", 0), b"fixture", "fixture")

        assert next_client.recv() == "Received"
        assert failed.closed and next_peer.closed
    finally:
        for peer in (failed, failed_client, next_peer, next_client):
            peer.close()

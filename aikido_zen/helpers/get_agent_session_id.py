from aikido_zen.helpers.uuid7 import uuid7

# Fork copies this value, so workers forked after import share one run.
_session_id = uuid7()


def get_agent_session_id():
    return _session_id


def set_agent_session_id(session_id):
    # pylint: disable=global-statement
    global _session_id
    _session_id = session_id

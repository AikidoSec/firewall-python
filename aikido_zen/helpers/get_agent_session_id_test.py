import os

import pytest

from aikido_zen.helpers.get_agent_session_id import get_agent_session_id


def test_session_id_stays_the_same():
    assert get_agent_session_id()
    assert get_agent_session_id() == get_agent_session_id()


@pytest.mark.skipif(not hasattr(os, "fork"), reason="fork is not available")
def test_forked_workers_share_the_session_id():
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        os.write(write_fd, get_agent_session_id().encode())
        os._exit(0)  # pylint: disable=protected-access

    os.close(write_fd)
    session_id = os.read(read_fd, 64).decode()
    os.close(read_fd)
    os.waitpid(pid, 0)

    assert session_id == get_agent_session_id()

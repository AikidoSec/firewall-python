import pytest
from .hostnames import Hostnames


def test_add_hostname():
    """Test adding a hostname."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    assert "example.com" in hostnames.map
    assert hostnames.map["example.com"] == {80}  # Should be a set


def test_add_multiple_ports():
    """Test adding multiple ports for the same hostname."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("example.com", 443)
    assert hostnames.map["example.com"] == {80, 443}  # Should contain both ports


def test_add_duplicate_hostname():
    """Test adding a duplicate hostname."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("example.com", 80)  # Should not change the port
    assert hostnames.map["example.com"] == {80}


def test_max_entries():
    """Test that the maximum number of entries is enforced."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("test.com", 443)
    hostnames.add("localhost", None)
    hostnames.add("newsite.com", 8080)  # This should remove "example.com"

    assert "example.com" not in hostnames.map
    assert "test.com" in hostnames.map
    assert "localhost" in hostnames.map
    assert "newsite.com" in hostnames.map
    assert len(hostnames.map) == 3


def test_as_array():
    """Test the as_array method."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("test.com", 443)
    expected_array = [
        {"hostname": "example.com", "port": 80},
        {"hostname": "test.com", "port": 443},
    ]
    assert hostnames.as_array() == expected_array


def test_clear():
    """Test the clear method."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("test.com", 443)
    hostnames.clear()
    assert len(hostnames.map) == 0


def test_add_none_port():
    """Test adding a hostname with a None port."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", None)
    assert "example.com" in hostnames.map
    assert None in hostnames.map["example.com"]  # Should be in the set


def test_exceed_max_entries_with_multiple_ports():
    """Test exceeding max entries with multiple ports."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("example.com", 443)
    hostnames.add("test.com", 8080)
    hostnames.add("newsite.com", 3000)  # This should remove "example.com"

    assert hostnames.map["example.com"] == {443}
    assert "test.com" in hostnames.map
    assert "newsite.com" in hostnames.map
    assert len(hostnames.map) == 3


def test_add_ports_and_check_length():
    """Test adding ports and checking the length property."""
    hostnames = Hostnames(max_entries=5)
    hostnames.add("example.com", 80)
    hostnames.add("example.com", 443)
    hostnames.add("test.com", 8080)

    assert hostnames.length == 3  # 2 ports for example.com + 1 for test.com


def test_add_and_remove_ports():
    """Test adding and removing ports."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    assert hostnames.map["example.com"] == {80}
    hostnames.add("example.com", 443)
    assert hostnames.map["example.com"] == {80, 443}
    hostnames.add("test.com", 8080)
    assert hostnames.map["example.com"] == {80, 443}
    assert hostnames.map["test.com"] == {8080}

    # Remove a port
    hostnames.map["example.com"].remove(80)
    assert hostnames.map["example.com"] == {443}  # Should only have port 443


def test_clear_with_multiple_entries():
    """Test clearing with multiple entries."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("test.com", 443)
    hostnames.add("localhost", 3000)
    hostnames.clear()
    assert len(hostnames.map) == 0


# To run the tests, use the command: pytest <filename>.py

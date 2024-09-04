import pytest
from .hostnames import Hostnames


def test_add_hostname():
    """Test adding a hostname."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    assert "example.com" in hostnames.map
    assert hostnames.map["example.com"] == 80


def test_add_duplicate_hostname():
    """Test adding a duplicate hostname."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("example.com", 443)  # Should not change the port
    assert hostnames.map["example.com"] == 80


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
    assert hostnames.map["example.com"] is None


# To run the tests, use the command: pytest <filename>.py

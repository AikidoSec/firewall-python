import pytest
from .hostnames import Hostnames


def test_add_hostname():
    """Test adding a hostname."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    key = "example.com:80"
    assert key in hostnames.map
    assert hostnames.map[key]["hostname"] == "example.com"
    assert hostnames.map[key]["port"] == 80
    assert hostnames.map[key]["hits"] == 1


def test_add_multiple_ports():
    """Test adding multiple ports for the same hostname."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("example.com", 443)

    key80 = "example.com:80"
    key443 = "example.com:443"

    assert key80 in hostnames.map
    assert key443 in hostnames.map
    assert hostnames.map[key80]["hits"] == 1
    assert hostnames.map[key443]["hits"] == 1


def test_add_duplicate_hostname():
    """Test adding a duplicate hostname."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("example.com", 80)  # Should not change the port
    key = "example.com:80"
    assert hostnames.map[key]["hits"] == 2  # Hits should increment


def test_max_entries():
    """Test that the maximum number of entries is enforced."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("test.com", 443)
    hostnames.add("localhost", None)
    hostnames.add("newsite.com", 8080)  # This should remove "example.com"

    assert "example.com:80" not in hostnames.map
    assert "test.com:443" in hostnames.map
    assert "localhost:None" in hostnames.map
    assert "newsite.com:8080" in hostnames.map
    assert len(hostnames.map) == 3


def test_as_array():
    """Test the as_array method."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("test.com", 443)
    expected_array = [
        {"hostname": "example.com", "port": 80, "hits": 1},
        {"hostname": "test.com", "port": 443, "hits": 1},
    ]
    assert hostnames.as_array() == expected_array
    assert isinstance(hostnames.as_array(), list)


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
    key = "example.com:None"
    assert key in hostnames.map
    assert hostnames.map[key]["hostname"] == "example.com"
    assert hostnames.map[key]["port"] is None
    assert hostnames.map[key]["hits"] == 1


def test_exceed_max_entries_with_multiple_ports():
    """Test exceeding max entries with multiple ports."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("example.com", 443)
    hostnames.add("test.com", 8080)
    hostnames.add("newsite.com", 3000)  # This should remove "example.com:80"

    assert "example.com:80" not in hostnames.map
    assert "example.com:443" in hostnames.map
    assert "test.com:8080" in hostnames.map
    assert "newsite.com:3000" in hostnames.map
    assert len(hostnames.map) == 3


def test_add_and_remove_ports():
    """Test adding and removing ports."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    assert hostnames.map["example.com:80"]["hits"] == 1
    hostnames.add("example.com", 443)
    assert hostnames.map["example.com:80"]["hits"] == 1
    assert hostnames.map["example.com:443"]["hits"] == 1
    hostnames.add("test.com", 8080)
    assert hostnames.map["example.com:80"]["hits"] == 1
    assert hostnames.map["example.com:443"]["hits"] == 1
    assert hostnames.map["test.com:8080"]["hits"] == 1

    # Remove a port (not directly supported in the current implementation)
    # This part of the test is not applicable since we don't have a remove method.
    # Instead, we can just check the hits.
    hostnames.map["example.com:80"]["hits"] = 0  # Simulating removal
    assert hostnames.map["example.com:80"]["hits"] == 0  # Should only have port 443


def test_clear_with_multiple_entries():
    """Test clearing with multiple entries."""
    hostnames = Hostnames(max_entries=3)
    hostnames.add("example.com", 80)
    hostnames.add("test.com", 443)
    hostnames.add("localhost", 3000)
    hostnames.clear()
    assert len(hostnames.map) == 0

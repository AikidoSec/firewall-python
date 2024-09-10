import time
import pytest
from .users import Users  # Assuming the Users class is in a file named users.py


@pytest.fixture
def users():
    """Fixture to create a Users instance with a max of 2 entries."""
    return Users(max_entries=2)


def test_users(users, monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 1
    )
    assert users.as_array() == []

    users.add_user({"id": "1", "name": "John", "lastIpAddress": "::1"})
    user1 = users.as_array()[0]
    assert user1["id"] == "1"
    assert user1["name"] == "John"
    assert user1["lastIpAddress"] == "::1"
    assert user1["lastSeenAt"] == user1["firstSeenAt"] == 1

    # Simulate the passage of time
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 2
    )
    users.add_user({"id": "1", "name": "John Doe", "lastIpAddress": "1.2.3.4"})
    user1_updated = users.as_array()[0]
    assert user1_updated["id"] == "1"
    assert user1_updated["name"] == "John Doe"
    assert user1_updated["lastIpAddress"] == "1.2.3.4"
    assert user1_updated["lastSeenAt"] == 2
    assert user1_updated["firstSeenAt"] == 1

    users.add_user({"id": "2", "name": "Jane", "lastIpAddress": "1.2.3.4"})
    user2 = users.as_array()[1]
    assert user2["id"] == "2"
    assert user2["name"] == "Jane"
    assert user2["lastIpAddress"] == "1.2.3.4"
    assert (
        user2["lastSeenAt"] >= user2["firstSeenAt"]
    )  # lastSeenAt should be >= firstSeenAt
    assert (
        user2["lastSeenAt"] == user2["firstSeenAt"]
    )  # Initially, they should be equal

    users.add_user({"id": "3", "name": "Alice", "lastIpAddress": "1.2.3.4"})
    user2_updated = users.as_array()[0]  # Jane should still be the first user
    user3 = users.as_array()[1]  # Alice should be the second user
    assert user2_updated["id"] == "2"
    assert user2_updated["name"] == "Jane"
    assert user2_updated["lastIpAddress"] == "1.2.3.4"
    assert (
        user2_updated["lastSeenAt"] >= user2_updated["firstSeenAt"]
    )  # lastSeenAt should be >= firstSeenAt
    assert (
        user2_updated["lastSeenAt"] == user2_updated["firstSeenAt"]
    )  # Should still be equal

    assert user3["id"] == "3"
    assert user3["name"] == "Alice"
    assert user3["lastIpAddress"] == "1.2.3.4"
    assert (
        user3["lastSeenAt"] >= user3["firstSeenAt"]
    )  # lastSeenAt should be >= firstSeenAt
    assert user3["lastSeenAt"] == user3["firstSeenAt"]  # Should be equal

    users.clear()
    assert users.as_array() == []

import time

import pytest
from datetime import datetime
from .users import Users


@pytest.fixture
def users():
    return Users(max_entries=3)


def test_add_user(users):
    user_id = "1"
    user_name = "Test User"
    user_ip = "127.0.0.1"
    current_time = datetime.now()

    users.add_user(user_id, user_name, user_ip, current_time)

    assert user_id in users.users
    assert users.users[user_id]["name"] == user_name
    assert users.users[user_id]["lastIpAddress"] == user_ip
    assert users.users[user_id]["firstSeenAt"] == current_time
    assert users.users[user_id]["lastSeenAt"] == current_time


def test_add_existing_user(users):
    user_id = "1"
    user_name = "Test User"
    user_ip = "127.0.0.1"
    current_time = datetime.now()

    users.add_user(user_id, user_name, user_ip, current_time)

    new_user_ip = "192.168.1.1"
    new_current_time = datetime.now()

    users.add_user(user_id, user_name, new_user_ip, new_current_time)

    assert user_id in users.users
    assert users.users[user_id]["name"] == user_name
    assert users.users[user_id]["lastIpAddress"] == new_user_ip
    assert users.users[user_id]["firstSeenAt"] == current_time
    assert users.users[user_id]["lastSeenAt"] == new_current_time


def test_ensure_max_entries(users):
    user_id_1 = "1"
    user_name_1 = "Test User 1"
    user_ip_1 = "127.0.0.1"
    current_time_1 = datetime.now()

    user_id_2 = "2"
    user_name_2 = "Test User 2"
    user_ip_2 = "192.168.1.1"
    current_time_2 = datetime.now()

    user_id_3 = "3"
    user_name_3 = "Test User 3"
    user_ip_3 = "10.0.0.1"
    current_time_3 = datetime.now()

    user_id_4 = "4"
    user_name_4 = "Test User 4"
    user_ip_4 = "172.16.0.1"
    current_time_4 = datetime.now()

    users.add_user(user_id_1, user_name_1, user_ip_1, current_time_1)
    users.add_user(user_id_2, user_name_2, user_ip_2, current_time_2)
    users.add_user(user_id_3, user_name_3, user_ip_3, current_time_3)
    users.add_user(user_id_4, user_name_4, user_ip_4, current_time_4)

    assert user_id_1 not in users.users
    assert user_id_2 in users.users
    assert user_id_3 in users.users
    assert user_id_4 in users.users


def test_as_array(users):
    user_id = "1"
    user_name = "Test User"
    user_ip = "127.0.0.1"
    current_time = datetime.now()

    users.add_user(user_id, user_name, user_ip, current_time)

    user_array = users.as_array()

    assert len(user_array) == 1
    assert user_array[0]["id"] == user_id
    assert user_array[0]["name"] == user_name
    assert user_array[0]["lastIpAddress"] == user_ip
    assert user_array[0]["firstSeenAt"] == current_time
    assert user_array[0]["lastSeenAt"] == current_time


def test_clear(users):
    user_id = "1"
    user_name = "Test User"
    user_ip = "127.0.0.1"
    current_time = datetime.now()

    users.add_user(user_id, user_name, user_ip, current_time)

    users.clear()

    assert len(users.users) == 0


def test_add_user_with_different_times(users):
    user_id = "1"
    user_name = "Test User"
    user_ip = "127.0.0.1"
    current_time_1 = datetime(2023, 1, 1, 12, 0, 0)
    current_time_2 = datetime(2023, 1, 2, 12, 0, 0)

    users.add_user(user_id, user_name, user_ip, current_time_1)
    users.add_user(user_id, user_name, user_ip, current_time_2)

    assert user_id in users.users
    assert users.users[user_id]["firstSeenAt"] == current_time_1
    assert users.users[user_id]["lastSeenAt"] == current_time_2


def test_add_multiple_users(users):
    user_id_1 = "1"
    user_name_1 = "Test User 1"
    user_ip_1 = "127.0.0.1"
    current_time_1 = datetime.now()

    user_id_2 = "2"
    user_name_2 = "Test User 2"
    user_ip_2 = "192.168.1.1"
    current_time_2 = datetime.now()

    users.add_user(user_id_1, user_name_1, user_ip_1, current_time_1)
    users.add_user(user_id_2, user_name_2, user_ip_2, current_time_2)

    assert user_id_1 in users.users
    assert user_id_2 in users.users
    assert users.users[user_id_1]["name"] == user_name_1
    assert users.users[user_id_2]["name"] == user_name_2


def test_ensure_max_entries_with_duplicate_users(users):
    user_id = "1"
    user_name = "Test User"
    user_ip = "127.0.0.1"
    current_time = datetime.now()

    users.add_user(user_id, user_name, user_ip, current_time)
    users.add_user(user_id, user_name, user_ip, current_time)
    users.add_user(user_id, user_name, user_ip, current_time)

    assert len(users.users) == 1
    assert user_id in users.users


def test_as_array_with_multiple_users(users):
    user_id_1 = "1"
    user_name_1 = "Test User 1"
    user_ip_1 = "127.0.0.1"
    current_time_1 = datetime.now()

    user_id_2 = "2"
    user_name_2 = "Test User 2"
    user_ip_2 = "192.168.1.1"
    current_time_2 = datetime.now()

    users.add_user(user_id_1, user_name_1, user_ip_1, current_time_1)
    users.add_user(user_id_2, user_name_2, user_ip_2, current_time_2)

    user_array = users.as_array()

    assert len(user_array) == 2
    assert user_array[0]["id"] == user_id_1
    assert user_array[1]["id"] == user_id_2


def test_clear_with_multiple_users(users):
    user_id_1 = "1"
    user_name_1 = "Test User 1"
    user_ip_1 = "127.0.0.1"
    current_time_1 = datetime.now()

    user_id_2 = "2"
    user_name_2 = "Test User 2"
    user_ip_2 = "192.168.1.1"
    current_time_2 = datetime.now()

    users.add_user(user_id_1, user_name_1, user_ip_1, current_time_1)
    users.add_user(user_id_2, user_name_2, user_ip_2, current_time_2)

    users.clear()

    assert len(users.users) == 0


def test_add_user_with_empty_name(users):
    user_id = "1"
    user_name = ""
    user_ip = "127.0.0.1"
    current_time = datetime.now()

    users.add_user(user_id, user_name, user_ip, current_time)

    assert user_id in users.users
    assert users.users[user_id]["name"] == user_name


def test_add_user_with_empty_ip(users):
    user_id = "1"
    user_name = "Test User"
    user_ip = ""
    current_time = datetime.now()

    users.add_user(user_id, user_name, user_ip, current_time)

    assert user_id in users.users
    assert users.users[user_id]["lastIpAddress"] == user_ip


def test_add_user_from_entry_new_user(users):
    user_entry = {
        "id": "1",
        "name": "Test User",
        "lastIpAddress": "127.0.0.1",
        "firstSeenAt": datetime.now(),
        "lastSeenAt": datetime.now(),
    }

    users.add_user_from_entry(user_entry)

    assert "1" in users.users
    assert users.users["1"]["name"] == "Test User"
    assert users.users["1"]["lastIpAddress"] == "127.0.0.1"


def test_add_user_from_entry_existing_user(users):
    user_id = "1"
    user_name = "Test User"
    user_ip = "127.0.0.1"
    current_time = datetime.now()

    users.add_user(user_id, user_name, user_ip, current_time)

    new_user_entry = {
        "id": "1",
        "name": "Updated User",
        "lastIpAddress": "192.168.1.1",
        "firstSeenAt": datetime.now(),
        "lastSeenAt": datetime.now(),
    }
    time.sleep(0.2)
    users.add_user_from_entry(new_user_entry)

    assert "1" in users.users
    assert users.users["1"]["name"] == "Updated User"
    assert users.users["1"]["lastIpAddress"] == "192.168.1.1"
    assert users.users["1"]["firstSeenAt"] == current_time


def test_add_user_from_entry_ensure_max_entries(users):
    user_entry_1 = {
        "id": "1",
        "name": "Test User 1",
        "lastIpAddress": "127.0.0.1",
        "firstSeenAt": datetime.now(),
        "lastSeenAt": datetime.now(),
    }

    user_entry_2 = {
        "id": "2",
        "name": "Test User 2",
        "lastIpAddress": "192.168.1.1",
        "firstSeenAt": datetime.now(),
        "lastSeenAt": datetime.now(),
    }

    user_entry_3 = {
        "id": "3",
        "name": "Test User 3",
        "lastIpAddress": "10.0.0.1",
        "firstSeenAt": datetime.now(),
        "lastSeenAt": datetime.now(),
    }

    user_entry_4 = {
        "id": "4",
        "name": "Test User 4",
        "lastIpAddress": "172.16.0.1",
        "firstSeenAt": datetime.now(),
        "lastSeenAt": datetime.now(),
    }

    users.add_user_from_entry(user_entry_1)
    users.add_user_from_entry(user_entry_2)
    users.add_user_from_entry(user_entry_3)
    users.add_user_from_entry(user_entry_4)

    assert "1" not in users.users
    assert "2" in users.users
    assert "3" in users.users
    assert "4" in users.users

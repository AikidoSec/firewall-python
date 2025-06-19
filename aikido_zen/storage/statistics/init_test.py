import pytest
from . import Statistics, Operations


@pytest.fixture
def stats():
    return Statistics()


def test_initialization(monkeypatch):
    # Mock the current time
    mock_time = 1234567890000
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: mock_time
    )

    stats = Statistics()
    assert stats.total_hits == 0
    assert stats.attacks_detected == 0
    assert stats.attacks_blocked == 0
    assert stats.started_at == mock_time
    assert isinstance(stats.operations, Operations)


def test_clear(monkeypatch):
    # Mock the current time
    mock_time = 1234567890000
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: mock_time
    )

    stats = Statistics()
    stats.total_hits = 10
    stats.attacks_detected = 5
    stats.attacks_blocked = 3
    stats.operations.register_call("test", "sql_op")
    stats.clear()

    assert stats.total_hits == 0
    assert stats.attacks_detected == 0
    assert stats.attacks_blocked == 0
    assert stats.started_at == mock_time
    assert stats.operations == {}


def test_increment_total_hits():
    stats = Statistics()
    stats.increment_total_hits()
    assert stats.total_hits == 1


def test_on_detected_attack(stats):
    stats.on_detected_attack(blocked=True, operation="test_op")
    assert stats.attacks_detected == 1
    assert stats.attacks_blocked == 1

    stats.on_detected_attack(blocked=False, operation="test_op")
    assert stats.attacks_detected == 2
    assert stats.attacks_blocked == 1


def test_get_record(monkeypatch):
    # Mock the current time
    mock_time = 1234567890000
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: mock_time
    )

    stats = Statistics()
    stats.total_hits = 10
    stats.on_rate_limit()
    stats.on_rate_limit()
    stats.operations.register_call("test.test", "nosql_op")
    stats.on_detected_attack(blocked=True, operation="test.test")
    stats.attacks_detected = 5
    stats.attacks_blocked = 3

    record = stats.get_record()
    assert record["startedAt"] == stats.started_at
    assert record["endedAt"] == mock_time
    assert record["requests"]["total"] == 10
    assert record["requests"]["rateLimited"] == 2
    assert record["requests"]["aborted"] == 0
    assert record["requests"]["attacksDetected"]["total"] == 5
    assert record["requests"]["attacksDetected"]["blocked"] == 3
    assert record["operations"] == {
        "test.test": {
            "attacksDetected": {"blocked": 1, "total": 1},
            "kind": "nosql_op",
            "total": 1,
        }
    }


def test_import_from_record():
    stats = Statistics()
    stats.operations.register_call("test.test", "nosql_op")
    stats.operations.register_call("test.test", "nosql_op")
    stats.operations.register_call("test.test", "nosql_op")
    record = {
        "requests": {
            "total": 10,
            "rateLimited": 5,
            "attacksDetected": {
                "total": 5,
                "blocked": 3,
            },
        },
        "operations": {
            "test.test": {
                "attacksDetected": {"blocked": 1, "total": 1},
                "kind": "nosql_op",
                "total": 1,
            },
            "test.test2": {
                "kind": "sql_op",
                "total": 5,
                "attacksDetected": {"blocked": 5, "total": 200},
            },
        },
    }
    stats.import_from_record(record)
    assert stats.total_hits == 10
    assert stats.rate_limited_hits == 5
    assert stats.attacks_detected == 5
    assert stats.attacks_blocked == 3
    assert stats.operations == {
        "test.test": {
            "attacksDetected": {"blocked": 1, "total": 1},
            "kind": "nosql_op",
            "total": 4,
        },
        "test.test2": {
            "kind": "sql_op",
            "total": 5,
            "attacksDetected": {"blocked": 5, "total": 200},
        },
    }


def test_empty(stats):
    assert stats.empty() == True

    stats.total_hits = 1
    assert stats.empty() == False

    stats.total_hits = 0
    stats.attacks_detected = 1
    assert stats.empty() == False

    stats.attacks_detected = 0
    stats.operations = {"test_op": {"total": 1}}
    assert stats.empty() == False


def test_multiple_imports(stats):
    record1 = {
        "requests": {
            "total": 10,
            "rateLimited": 20,
            "attacksDetected": {
                "total": 5,
                "blocked": 3,
            },
        },
        "operations": {
            "test_op1": {
                "total": 1,
                "kind": "fs_op",
                "attacksDetected": {"total": 0, "blocked": 0},
            }
        },
    }
    record2 = {
        "requests": {
            "total": 20,
            "rateLimited": 5,
            "attacksDetected": {
                "total": 10,
                "blocked": 7,
            },
        },
        "operations": {
            "test_op2": {
                "total": 1,
                "kind": "fs_op",
                "attacksDetected": {"total": 0, "blocked": 0},
            }
        },
    }
    stats.import_from_record(record1)
    stats.import_from_record(record2)
    assert stats.total_hits == 30
    assert stats.rate_limited_hits == 25
    assert stats.attacks_detected == 15
    assert stats.attacks_blocked == 10
    assert stats.operations == {
        "test_op1": {
            "attacksDetected": {"blocked": 0, "total": 0},
            "kind": "fs_op",
            "total": 1,
        },
        "test_op2": {
            "attacksDetected": {"blocked": 0, "total": 0},
            "kind": "fs_op",
            "total": 1,
        },
    }


def test_import_empty_record(stats):
    record = {"requests": {}}
    stats.import_from_record(record)
    assert stats.total_hits == 0
    assert stats.rate_limited_hits == 0
    assert stats.attacks_detected == 0
    assert stats.attacks_blocked == 0
    assert stats.operations == {}


def test_import_partial_record(stats):
    record = {"requests": {"total": 10}}
    stats.import_from_record(record)
    assert stats.total_hits == 10
    assert stats.rate_limited_hits == 0
    assert stats.attacks_detected == 0
    assert stats.attacks_blocked == 0
    assert stats.operations == {}


def test_increment_and_detect(stats):
    stats.increment_total_hits()
    stats.on_detected_attack(blocked=True, operation="test_op")
    assert stats.total_hits == 1
    assert stats.attacks_detected == 1
    assert stats.attacks_blocked == 1


def test_multiple_increments_and_detects(stats):
    stats.operations.register_call("test_op", "sql_op")
    for _ in range(10):
        stats.increment_total_hits()
    for _ in range(5):
        stats.on_detected_attack(blocked=True, operation="test_op")
    for _ in range(5):
        stats.on_detected_attack(blocked=False, operation="test_op")
    assert stats.total_hits == 10
    assert stats.attacks_detected == 10
    assert stats.attacks_blocked == 5
    assert stats.operations.get("test_op") == {
        "attacksDetected": {"blocked": 5, "total": 10},
        "kind": "sql_op",
        "total": 1,
    }

    stats.on_rate_limit()
    assert stats.rate_limited_hits == 1

    stats.on_rate_limit()
    assert stats.rate_limited_hits == 2


def test_multiple_rate_limits(stats):
    """Test multiple rate limit calls"""
    for _ in range(5):
        stats.on_rate_limit()
    assert stats.rate_limited_hits == 5


def test_rate_limit_in_get_record():
    """Test that rate_limited_hits is included in get_record output"""
    stats = Statistics()
    stats.total_hits = 10
    stats.on_rate_limit()
    stats.on_rate_limit()
    stats.on_rate_limit()

    record = stats.get_record()
    assert record["requests"]["rateLimited"] == 3
    assert record["requests"]["total"] == 10


def test_rate_limit_clear():
    """Test that clear() resets rate_limited_hits"""
    stats = Statistics()
    stats.on_rate_limit()
    stats.on_rate_limit()
    assert stats.rate_limited_hits == 2

    stats.clear()
    assert stats.rate_limited_hits == 0

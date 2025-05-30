import pytest
from . import Statistics


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
    stats.clear()

    assert stats.total_hits == 0
    assert stats.attacks_detected == 0
    assert stats.attacks_blocked == 0
    assert stats.started_at == mock_time


def test_increment_total_hits():
    stats = Statistics()
    stats.increment_total_hits()
    assert stats.total_hits == 1


def test_on_detected_attack():
    stats = Statistics()
    stats.on_detected_attack(blocked=True)
    assert stats.attacks_detected == 1
    assert stats.attacks_blocked == 1

    stats.on_detected_attack(blocked=False)
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
    stats.attacks_detected = 5
    stats.attacks_blocked = 3

    record = stats.get_record()
    assert record["startedAt"] == stats.started_at
    assert record["endedAt"] == mock_time
    assert record["requests"]["total"] == 10
    assert record["requests"]["aborted"] == 0
    assert record["requests"]["attacksDetected"]["total"] == 5
    assert record["requests"]["attacksDetected"]["blocked"] == 3


def test_import_from_record():
    stats = Statistics()
    record = {
        "requests": {
            "total": 10,
            "attacksDetected": {
                "total": 5,
                "blocked": 3,
            },
        }
    }
    stats.import_from_record(record)
    assert stats.total_hits == 10
    assert stats.attacks_detected == 5
    assert stats.attacks_blocked == 3


def test_empty():
    stats = Statistics()
    assert stats.empty() == True

    stats.total_hits = 1
    assert stats.empty() == False

    stats.total_hits = 0
    stats.attacks_detected = 1
    assert stats.empty() == False


def test_multiple_imports():
    stats = Statistics()
    record1 = {
        "requests": {
            "total": 10,
            "attacksDetected": {
                "total": 5,
                "blocked": 3,
            },
        }
    }
    record2 = {
        "requests": {
            "total": 20,
            "attacksDetected": {
                "total": 10,
                "blocked": 7,
            },
        }
    }
    stats.import_from_record(record1)
    stats.import_from_record(record2)
    assert stats.total_hits == 30
    assert stats.attacks_detected == 15
    assert stats.attacks_blocked == 10


def test_import_empty_record():
    stats = Statistics()
    record = {"requests": {}}
    stats.import_from_record(record)
    assert stats.total_hits == 0
    assert stats.attacks_detected == 0
    assert stats.attacks_blocked == 0


def test_import_partial_record():
    stats = Statistics()
    record = {"requests": {"total": 10}}
    stats.import_from_record(record)
    assert stats.total_hits == 10
    assert stats.attacks_detected == 0
    assert stats.attacks_blocked == 0


def test_increment_and_detect():
    stats = Statistics()
    stats.increment_total_hits()
    stats.on_detected_attack(blocked=True)
    assert stats.total_hits == 1
    assert stats.attacks_detected == 1
    assert stats.attacks_blocked == 1


def test_multiple_increments_and_detects():
    stats = Statistics()
    for _ in range(10):
        stats.increment_total_hits()
    for _ in range(5):
        stats.on_detected_attack(blocked=True)
    for _ in range(5):
        stats.on_detected_attack(blocked=False)
    assert stats.total_hits == 10
    assert stats.attacks_detected == 10
    assert stats.attacks_blocked == 5

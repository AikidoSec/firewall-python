import pytest
from queue import Queue
from unittest.mock import MagicMock
from .attack import process_attack


class MockCloudConnectionManager:
    def __init__(self):
        self.statistics = MagicMock()


def test_process_attack_adds_data_to_queue():
    queue = Queue()
    connection_manager = MockCloudConnectionManager()
    data = ("injection_results", "context", True, "stacktrace")  # Example data
    process_attack(connection_manager, data, queue)

    # Check if the data is added to the queue
    assert not queue.empty()
    assert queue.get() == data


def test_process_attack_statistics_called_when_enabled():
    queue = Queue()
    connection_manager = MockCloudConnectionManager()
    data = ("injection_results", "context", True, "stacktrace")  # Example data
    process_attack(connection_manager, data, queue)

    # Check if on_detected_attack was called
    connection_manager.statistics.on_detected_attack.assert_called_once_with(
        blocked=True
    )


def test_process_attack_statistics_not_called_when_disabled():
    queue = Queue()
    connection_manager = MockCloudConnectionManager()
    connection_manager.statistics = None  # Disable statistics
    data = ("injection_results", "context", True, "stacktrace")  # Example data
    process_attack(connection_manager, data, queue)

    # Check if on_detected_attack was not called
    assert (
        connection_manager.statistics is None
        or not connection_manager.statistics.on_detected_attack.called
    )


def test_process_attack_multiple_calls():
    queue = Queue()
    connection_manager = MockCloudConnectionManager()
    data1 = ("injection_results_1", "context_1", True, "stacktrace_1")
    data2 = ("injection_results_2", "context_2", False, "stacktrace_2")

    process_attack(connection_manager, data1, queue)
    process_attack(connection_manager, data2, queue)

    # Check if both data items are added to the queue
    assert queue.qsize() == 2
    assert queue.get() == data1
    assert queue.get() == data2


def test_process_attack_with_different_data_formats():
    queue = Queue()
    connection_manager = MockCloudConnectionManager()

    # Test with different types of data
    data1 = ("injection_results", "context", True, "stacktrace")
    data2 = ("injection_results", "context", False, "stacktrace")
    data3 = ("injection_results", "context", None, "stacktrace")

    process_attack(connection_manager, data1, queue)
    process_attack(connection_manager, data2, queue)
    process_attack(connection_manager, data3, queue)

    # Check if all data items are added to the queue
    assert queue.qsize() == 3
    assert queue.get() == data1
    assert queue.get() == data2
    assert queue.get() == data3

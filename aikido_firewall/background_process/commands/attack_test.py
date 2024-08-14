import pytest
from queue import Queue
from unittest.mock import MagicMock
from .attack import process_attack


class MockReporter:
    def __init__(self):
        self.statistics = MagicMock()


class MockBgProcess:
    def __init__(self):
        self.queue = Queue()
        self.reporter = MockReporter()


def test_process_attack_adds_data_to_queue():
    bg_process = MockBgProcess()
    data = ("attack_type", "source_ip", True)  # Example data
    process_attack(bg_process, data, None)

    # Check if the data is added to the queue
    assert not bg_process.queue.empty()
    assert bg_process.queue.get() == data


def test_process_attack_statistics_called_when_enabled():
    bg_process = MockBgProcess()
    data = ("attack_type", "source_ip", True)  # Example data
    process_attack(bg_process, data, None)

    # Check if on_detected_attack was called
    bg_process.reporter.statistics.on_detected_attack.assert_called_once_with(
        blocked=True
    )


def test_process_attack_statistics_not_called_when_disabled():
    bg_process = MockBgProcess()
    bg_process.reporter.statistics = None  # Disable statistics
    data = ("attack_type", "source_ip", True)  # Example data
    process_attack(bg_process, data, None)

    # Check if on_detected_attack was not called
    assert (
        bg_process.reporter.statistics is None
        or not bg_process.reporter.statistics.on_detected_attack.called
    )


def test_process_attack_multiple_calls():
    bg_process = MockBgProcess()
    data1 = ("attack_type_1", "source_ip_1", True)
    data2 = ("attack_type_2", "source_ip_2", False)

    process_attack(bg_process, data1, None)
    process_attack(bg_process, data2, None)

    # Check if both data items are added to the queue
    assert bg_process.queue.qsize() == 2
    assert bg_process.queue.get() == data1
    assert bg_process.queue.get() == data2


def test_process_attack_with_different_data_formats():
    bg_process = MockBgProcess()

    # Test with different types of data
    data1 = ("attack_type", "source_ip", True)
    data2 = ("attack_type", "source_ip", False)
    data3 = ("attack_type", "source_ip", None)

    process_attack(bg_process, data1, None)
    process_attack(bg_process, data2, None)
    process_attack(bg_process, data3, None)

    # Check if all data items are added to the queue
    assert bg_process.queue.qsize() == 3
    assert bg_process.queue.get() == data1
    assert bg_process.queue.get() == data2
    assert bg_process.queue.get() == data3


# Run the tests
if __name__ == "__main__":
    pytest.main()

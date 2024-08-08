import pytest
from unittest.mock import MagicMock, patch
from .attack import process_attack


@pytest.fixture
def mock_bg_process():
    class MockQueue:
        def __init__(self):
            self.items = []

        def put(self, item):
            self.items.append(item)

    bg_process = MagicMock()
    bg_process.queue = MockQueue()
    return bg_process


def test_process_attack_adds_data_to_queue(mock_bg_process):
    data = {"attack_type": "SQL Injection", "details": "Some details about the attack"}
    process_attack(mock_bg_process, data)

    assert len(mock_bg_process.queue.items) == 1
    assert mock_bg_process.queue.items[0] == data


def test_process_attack_with_multiple_calls(mock_bg_process):
    data1 = {"attack_type": "XSS", "details": "Some details about XSS"}
    data2 = {"attack_type": "DDoS", "details": "Some details about DDoS"}
    process_attack(mock_bg_process, data1)
    process_attack(mock_bg_process, data2)

    assert len(mock_bg_process.queue.items) == 2
    assert mock_bg_process.queue.items[0] == data1
    assert mock_bg_process.queue.items[1] == data2

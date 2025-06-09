import pytest
from .operations import Operations


@pytest.fixture
def operations():
    return Operations()


def test_ensure_operation(operations):
    operation = "test_op"
    kind = "sql_op"
    operations.ensure_operation(operation, kind)
    assert operation in operations
    assert operations[operation]["kind"] == kind
    assert operations[operation]["total"] == 0
    assert operations[operation]["attacksDetected"]["total"] == 0
    assert operations[operation]["attacksDetected"]["blocked"] == 0


def test_ensure_operation_unsupported_kind(operations):
    operation = "test_op"
    kind = "unsupported_kind"
    with pytest.raises(Exception):
        operations.ensure_operation(operation, kind)


def test_register_call(operations):
    operation = "test_op"
    kind = "sql_op"
    operations.register_call(operation, kind)
    assert operation in operations
    assert operations[operation]["total"] == 1


def test_on_detected_attack(operations):
    operation = "test_op"
    kind = "ai_op"
    operations.ensure_operation(operation, kind)
    operations.on_detected_attack(blocked=True, operation=operation)
    assert operations[operation]["attacksDetected"]["total"] == 1
    assert operations[operation]["attacksDetected"]["blocked"] == 1


def test_on_detected_attack_not_blocked(operations):
    operation = "test_op"
    kind = "sql_op"
    operations.ensure_operation(operation, kind)
    operations.on_detected_attack(blocked=False, operation=operation)
    assert operations[operation]["attacksDetected"]["total"] == 1
    assert operations[operation]["attacksDetected"]["blocked"] == 0


def test_on_detected_attack_unknown_operation(operations):
    operation = "unknown_op"
    operations.on_detected_attack(blocked=True, operation=operation)
    assert operation not in operations


def test_register_call_and_on_detected_attack(operations):
    operation = "test_op"
    kind = "sql_op"
    operations.register_call(operation, kind)
    operations.on_detected_attack(blocked=True, operation=operation)
    assert operations[operation]["total"] == 1
    assert operations[operation]["attacksDetected"]["total"] == 1
    assert operations[operation]["attacksDetected"]["blocked"] == 1

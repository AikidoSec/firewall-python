import pytest
from .create_interval import create_interval, interval_loop
from unittest.mock import Mock, call


def test_create_interval_schedules_function():
    # Arrange
    event_scheduler = Mock()
    function = Mock()
    args = (1, 2)
    interval_in_secs = 5

    # Act
    create_interval(event_scheduler, interval_in_secs, function, args)

    # Assert
    event_scheduler.enter.assert_called_once_with(
        interval_in_secs,
        1,
        interval_loop,
        (event_scheduler, interval_in_secs, function, args),
    )


def test_interval_loop_executes_function_and_reschedules():
    # Arrange
    event_scheduler = Mock()
    function = Mock()
    args = (1, 2)
    interval_in_secs = 5

    # Act
    interval_loop(event_scheduler, interval_in_secs, function, args)

    # Assert
    function.assert_called_once_with(*args)
    event_scheduler.enter.assert_called_once_with(
        interval_in_secs,
        1,
        interval_loop,
        (event_scheduler, interval_in_secs, function, args),
    )


def test_multiple_calls_to_create_interval():
    # Arrange
    event_scheduler = Mock()
    function = Mock()
    args = (1, 2)
    interval_in_secs = 5

    # Act
    create_interval(event_scheduler, interval_in_secs, function, args)
    create_interval(event_scheduler, interval_in_secs, function, args)

    # Assert
    assert event_scheduler.enter.call_count == 2
    assert event_scheduler.enter.call_args_list == [
        call(
            interval_in_secs,
            1,
            interval_loop,
            (event_scheduler, interval_in_secs, function, args),
        ),
        call(
            interval_in_secs,
            1,
            interval_loop,
            (event_scheduler, interval_in_secs, function, args),
        ),
    ]


if __name__ == "__main__":
    pytest.main()

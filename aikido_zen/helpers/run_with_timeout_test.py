import time

from aikido_zen.helpers.run_with_timeout import run_with_timeout


def mock_function_succeed(arg1, arg2):
    return f"Success with {arg1} and {arg2}"


def mock_function_timeout(arg1, arg2):
    time.sleep(3)  # Simulate a long-running task
    return f"Success with {arg1} and {arg2}"


def mock_function_exception(arg1, arg2):
    raise ValueError("Something went wrong")


# Test case for successful execution
def test_run_with_timeout_succeed():
    args = ("arg1_value", "arg2_value")
    timeout = 5
    result = run_with_timeout(mock_function_succeed, args, timeout)
    assert result.success() == True
    assert result.result == "Success with arg1_value and arg2_value"
    assert result.error is None


# Test case for timeout
def test_run_with_timeout_timeout():
    args = ("arg1_value", "arg2_value")
    timeout = 1
    result = run_with_timeout(mock_function_timeout, args, timeout)
    assert result.success() == False
    assert result.result is None
    assert result.error == f"Timed out after {timeout} seconds"


# Test case for exception
def test_run_with_timeout_exception():
    args = ("arg1_value", "arg2_value")
    timeout = 5
    result = run_with_timeout(mock_function_exception, args, timeout)
    assert result.success() == False
    assert result.result is None
    assert isinstance(result.error, ValueError)
    assert str(result.error) == "Something went wrong"

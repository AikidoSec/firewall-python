import time

from aikido_zen.helpers.run_with_timeout import run_with_timeout


def mock_function_succeed(arg1, arg2):
    return f"Success with {arg1} and {arg2}"


def mock_function_timeout(arg1, arg2):
    time.sleep(20)  # Simulate a long-running task
    return f"Success with {arg1} and {arg2}"


def mock_function_exception(arg1, arg2):
    raise ValueError("Something went wrong")


# Test case for successful execution
def test_run_with_timeout_succeed():
    args = ("arg1_value", "arg2_value")
    timeout = 0.1
    result = run_with_timeout(mock_function_succeed, args, timeout)
    assert result.success() == True
    assert result.result == "Success with arg1_value and arg2_value"
    assert result.error is None


# Test case for timeout
def test_run_with_timeout_timeout():
    args = ("arg1_value", "arg2_value")
    timeout = 0.1
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


# Performance testing
def mock_function_immediate(arg1, arg2):
    return f"Immediate success with {arg1} and {arg2}"


def measure_overhead():
    args = ("arg1_value", "arg2_value")
    timeout = 5

    # Measure direct execution time
    start_time = time.time()
    result = mock_function_immediate(*args)
    end_time = time.time()
    direct_time = end_time - start_time

    # Measure execution time with run_with_timeout
    start_time = time.time()
    result_with_timeout = run_with_timeout(mock_function_immediate, args, timeout)
    end_time = time.time()
    timeout_time = end_time - start_time

    overhead = timeout_time - direct_time
    return overhead


def test_performance_overhead():
    num_tests = 100  # Number of tests to average
    overheads = []

    for _ in range(num_tests):
        overhead = measure_overhead()
        overheads.append(overhead)

    average_overhead = sum(overheads) / num_tests
    print(f"Average overhead of run_with_timeout: {average_overhead:.6f} seconds")
    assert average_overhead < 50 / 1000  # Ensure less than 50ms overhead

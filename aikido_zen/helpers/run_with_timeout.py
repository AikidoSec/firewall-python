import concurrent.futures


class RunnerResult:
    def __init__(self, result, error=None):
        self.result = result
        self.error = error

    def success(self):
        if self.error is not None:
            return False
        return True


def run_with_timeout(func, args, timeout) -> RunnerResult:
    """
    Runs `func` with `args` in a new thread pool
    Only runs for `timeout` seconds
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args)
        try:
            result = future.result(timeout=timeout)
            return RunnerResult(result)
        except concurrent.futures.TimeoutError:
            return RunnerResult(result=None, error=f"Timed out after {timeout} seconds")
        except Exception as e:
            return RunnerResult(result=None, error=e)

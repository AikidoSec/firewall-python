import multiprocessing


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
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=worker, args=(func, args, result_queue))
    process.start()
    process.join(timeout=timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        return RunnerResult(result=None, error=f"Timed out after {timeout} seconds")

    if result_queue.empty():
        return RunnerResult(
            result=None,
            error="worker process always adds value to queue, something went wrong.",
        )

    result, error = result_queue.get()
    if error is not None:
        return RunnerResult(result=None, error=error)
    return RunnerResult(result=result)


def worker(func, args, result_queue):
    try:
        result = func(*args)
        result_queue.put((result, None))
    except Exception as e:
        result_queue.put((None, e))

from unittest.mock import patch

import aikido_zen.thread.process_worker as process_worker
import aikido_zen.thread.thread_cache as thread_cache


def sleeps_over(iterations, config_loaded=False, clock_step=0):
    """Runs the worker loop and returns the sleep it chose on each pass"""
    slept = []

    def stop_eventually(seconds):
        slept.append(seconds)
        if len(slept) >= iterations:
            raise KeyboardInterrupt

    thread_cache.global_thread_cache.reset()
    if config_loaded:
        thread_cache.global_thread_cache.config.last_updated_at = 1

    clock = [0.0]

    def fake_monotonic():
        clock[0] += clock_step
        return clock[0]

    with patch("aikido_zen.thread.thread_cache.renew"), patch(
        "time.monotonic", side_effect=fake_monotonic
    ), patch("time.sleep", side_effect=stop_eventually):
        try:
            process_worker.aikido_process_worker_thread()
        except KeyboardInterrupt:
            pass
    return slept


def test_retries_quickly_while_waiting_for_the_first_config():
    assert sleeps_over(3) == [process_worker.INITIAL_CONFIG_RETRY_SECONDS] * 3


def test_uses_the_normal_interval_once_the_config_arrived():
    assert (
        sleeps_over(2, config_loaded=True)
        == [process_worker.RENEW_CACHE_EVERY_X_SEC] * 2
    )


def test_stops_retrying_quickly_when_the_config_never_arrives():
    sleeps = sleeps_over(
        2, clock_step=process_worker.INITIAL_CONFIG_RETRY_WINDOW_SECONDS
    )

    assert sleeps == [process_worker.RENEW_CACHE_EVERY_X_SEC] * 2

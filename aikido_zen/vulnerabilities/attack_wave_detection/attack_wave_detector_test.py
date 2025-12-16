import pytest
from unittest.mock import patch
from .attack_wave_detector import AttackWaveDetector
import aikido_zen.test_utils as test_utils


def new_attack_wave_detector():
    return AttackWaveDetector(
        attack_wave_threshold=6,
        attack_wave_time_frame=60 * 1000,
        min_time_between_events=60 * 60 * 1000,
        max_lru_entries=10_000,
    )


# Mock for get_unixtime_ms
def mock_get_unixtime_ms(monotonic=True, mock_time=0):
    return mock_time


def test_no_context():
    detector = new_attack_wave_detector()
    assert not detector.is_attack_wave(None)


def test_no_ip_address_in_context():
    detector = new_attack_wave_detector()
    context = test_utils.generate_context(ip=None)
    assert not detector.is_attack_wave(context)


def test_a_web_scanner():
    detector = new_attack_wave_detector()
    context = test_utils.generate_context()

    # Mock is_web_scanner to return True for this test
    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        # Is true because the threshold is 6
        assert detector.is_attack_wave(context)
        # False again because event should have been sent last time
        assert not detector.is_attack_wave(context)


def test_non_web_scanner():
    detector = new_attack_wave_detector()
    context = test_utils.generate_context()

    # Mock is_web_scanner to return False for this test
    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=False,
    ):
        # Should return False even after multiple calls because it's not a web scanner
        for _ in range(10):
            assert not detector.is_attack_wave(context)


def test_a_web_scanner_with_delays():
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        detector = new_attack_wave_detector()
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=30 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        assert not detector.is_attack_wave(context)
        # Is true because the threshold is 6
        assert detector.is_attack_wave(context)
        # False again because event should have been sent last time
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=60 * 60 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Still false because minimum time between events is 1 hour
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=92 * 60 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Should resend event after 1 hour
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert detector.is_attack_wave(context)


def test_unique_samples_only():
    """Test that only unique samples are stored (non-unique contexts aren't stored)"""
    detector = new_attack_wave_detector()

    # Create multiple contexts with the same method and URL
    context1 = test_utils.generate_context(method="GET")
    context2 = test_utils.generate_context(method="GET")  # Same as context1
    context3 = test_utils.generate_context(method="GET")  # Same as context1

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Make enough requests to trigger attack wave (threshold is 6)
        for i in range(6):
            detector.is_attack_wave(context1)

        # Make a few more identical requests with different context objects
        for i in range(3):
            detector.is_attack_wave(context2)
            detector.is_attack_wave(context3)

        # Should have only 1 unique sample despite 9 identical requests
        samples = detector.get_samples_for_ip(context1.remote_address)
        assert len(samples) == 1
        assert samples[0]["method"] == "GET"
        assert samples[0]["url"] == context1.url


def test_unique_samples_with_different_methods():
    """Test that different methods for the same URL are stored as separate samples"""
    detector = new_attack_wave_detector()

    # Create contexts with different methods (URL will be the same due to test_utils limitation)
    context_get = test_utils.generate_context(method="GET")
    context_post = test_utils.generate_context(method="POST")
    context_put = test_utils.generate_context(method="PUT")

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Make enough requests to trigger attack wave for each method
        for i in range(2):  # 2 requests per method = 6 total
            detector.is_attack_wave(context_get)
            detector.is_attack_wave(context_post)
            detector.is_attack_wave(context_put)

        # Should have 3 unique samples (one for each method)
        samples = detector.get_samples_for_ip(context_get.remote_address)
        assert len(samples) == 3

        # Verify each method is present
        methods = {sample["method"] for sample in samples}
        assert methods == {"GET", "POST", "PUT"}

        # All should have the same URL (due to test_utils limitation)
        for sample in samples:
            assert sample["url"] == context_get.url


def test_samples_max_length():
    """Test that samples are limited to maximum 10 samples"""
    detector = new_attack_wave_detector()

    # Create a helper function to create contexts with different URLs
    def create_context_with_url(url, method="GET"):
        from aikido_zen.context import Context
        from aikido_zen.helpers.headers import Headers

        headers = Headers()
        return Context(
            context_obj={
                "remote_address": "1.1.1.1",
                "method": method,
                "url": url,
                "query": {},
                "headers": headers,
                "body": None,
                "cookies": {},
                "source": "test",
                "route": "/test",
                "user": None,
                "executed_middleware": False,
                "parsed_userinput": {},
            }
        )

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Create 15 unique contexts (different URLs) with different IPs to avoid cooldown
        unique_contexts = []
        for i in range(15):
            url = f"http://localhost:8080/unique-route-{i}"
            context = create_context_with_url(
                url, f"METHOD{i % 5}"
            )  # Cycle through methods
            # Set different IP for each context to avoid cooldown
            context.remote_address = f"1.1.1.{i+1}"
            unique_contexts.append(context)

        # Make requests with all unique contexts (each one should trigger attack wave)
        for context in unique_contexts:
            # Need to make 6 requests per context to trigger attack wave
            for i in range(6):
                detector.is_attack_wave(context)

        # Check samples for the first IP - should have 1 sample
        samples = detector.get_samples_for_ip(unique_contexts[0].remote_address)
        assert len(samples) == 1

        # Verify sample structure
        sample = samples[0]
        assert set(sample.keys()) == {"method", "url"}
        assert sample["method"] == "METHOD0"
        assert sample["url"] == "http://localhost:8080/unique-route-0"


def test_samples_structure():
    """Test that samples contain correct structure with method and URL only"""
    detector = new_attack_wave_detector()

    # Create a context
    context = test_utils.generate_context(method="POST")

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Make enough requests to trigger attack wave
        for i in range(6):
            detector.is_attack_wave(context)

        # Get the samples
        samples = detector.get_samples_for_ip(context.remote_address)

        # Should have 1 sample
        assert len(samples) == 1

        # Verify sample structure (method and url only, no user_agent or timestamp)
        sample = samples[0]
        assert set(sample.keys()) == {"method", "url"}
        assert sample["method"] == "POST"
        assert sample["url"] == context.url
        assert "user_agent" not in sample
        assert "timestamp" not in sample


def test_mixed_unique_and_duplicate_samples():
    """Test mixed scenario with both unique and duplicate samples"""
    detector = new_attack_wave_detector()

    # Create a helper function to create contexts with different URLs
    def create_context_with_url(url, method="GET"):
        from aikido_zen.context import Context
        from aikido_zen.helpers.headers import Headers

        headers = Headers()
        return Context(
            context_obj={
                "remote_address": "1.1.1.1",
                "method": method,
                "url": url,
                "query": {},
                "headers": headers,
                "body": None,
                "cookies": {},
                "source": "test",
                "route": "/test",
                "user": None,
                "executed_middleware": False,
                "parsed_userinput": {},
            }
        )

    # Create some unique contexts
    context_env = create_context_with_url("http://localhost:8080/.env", "GET")
    context_git = create_context_with_url("http://localhost:8080/.git/config", "POST")
    context_htaccess = create_context_with_url("http://localhost:8080/.htaccess", "PUT")

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Add some unique samples (each needs 6 requests to trigger attack wave)
        # But use different IPs to avoid cooldown
        context_env.remote_address = "1.1.1.1"
        context_git.remote_address = "1.1.1.2"
        context_htaccess.remote_address = "1.1.1.3"

        for i in range(6):
            detector.is_attack_wave(context_env)

        for i in range(6):
            detector.is_attack_wave(context_git)

        for i in range(6):
            detector.is_attack_wave(context_htaccess)

        # Add many duplicate requests for the first context (same IP)
        for i in range(10):
            detector.is_attack_wave(context_env)

        # Should have 1 unique sample for the first IP
        samples = detector.get_samples_for_ip(context_env.remote_address)
        assert len(samples) == 1

        # Verify the sample structure
        sample = samples[0]
        assert set(sample.keys()) == {"method", "url"}
        assert sample["method"] == "GET"
        assert sample["url"] == "http://localhost:8080/.env"
        assert "user_agent" not in sample
        assert "timestamp" not in sample


def test_samples_tracking():
    """Test that samples are tracked correctly"""
    detector = new_attack_wave_detector()
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Make a few requests
        for i in range(3):
            detector.is_attack_wave(context)

        # Check that samples are being tracked (should have only 1 unique sample)
        samples = detector.get_samples_for_ip(context.remote_address)
        assert len(samples) == 1  # Only 1 unique sample despite 3 identical requests
        assert samples[0]["method"] == "POST"
        assert samples[0]["url"] == "http://localhost:8080/"

        # Make more requests to exceed the sample limit
        for i in range(10):
            detector.is_attack_wave(context)

        # Should still have only the most recent samples (limited to 10)
        samples = detector.get_samples_for_ip(context.remote_address)
        assert len(samples) <= 10


def test_clear_samples():
    """Test that samples can be cleared"""
    detector = new_attack_wave_detector()
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Make some requests
        for i in range(5):
            detector.is_attack_wave(context)

        # Verify samples exist (should have only 1 unique sample)
        samples = detector.get_samples_for_ip(context.remote_address)
        assert len(samples) == 1  # Only 1 unique sample despite 5 identical requests

        # Clear samples
        detector.clear_samples_for_ip(context.remote_address)

        # Verify samples are cleared
        samples = detector.get_samples_for_ip(context.remote_address)
        assert len(samples) == 0


def test_a_slow_web_scanner_that_triggers_in_the_second_interval():
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        detector = new_attack_wave_detector()
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=62 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert detector.is_attack_wave(context)


def test_a_slow_web_scanner_that_triggers_in_the_third_interval():
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        detector = new_attack_wave_detector()
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=62 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Still false because minimum time between events is 1 hour
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=124 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Should resend event after 1 hour
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert detector.is_attack_wave(context)

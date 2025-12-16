import inspect

import pytest
from unittest.mock import patch, MagicMock
from aikido_zen.thread.thread_cache import get_cache, ThreadCache
from .request_handler import request_handler
from ...background_process.commands import process_check_firewall_lists
from ...background_process.service_config import ServiceConfig
from ...context import Context, current_context
from ...helpers.headers import Headers
from ...storage.firewall_lists import FirewallLists
from ...vulnerabilities.attack_wave_detection.attack_wave_detector import (
    AttackWaveDetector,
)


@pytest.fixture
def mock_context():
    """Fixture to create a mock context."""
    context = MagicMock()
    context.route = "/test/route"
    context.method = "GET"
    context.get_route_metadata.return_value = {
        "route": "/test/route",
        "method": "GET",
        "url": "http://localhost:8080/test/route",
    }
    context.body = {}
    return context


@pytest.fixture(autouse=True)
def run_around_tests():
    get_cache().reset()
    current_context.set(None)
    yield
    get_cache().reset()
    current_context.set(None)


class MyMockComms:
    def __init__(self):
        self.firewall_lists = FirewallLists()
        self.conn_manager = MagicMock()
        self.conn_manager.firewall_lists = self.firewall_lists
        self.conn_manager.attack_wave_detector = AttackWaveDetector()
        self.attacks = []

    def send_data_to_bg_process(self, action, obj, receive=False, timeout_in_sec=0.1):
        if action != "CHECK_FIREWALL_LISTS":
            return {"success": False}
        res = process_check_firewall_lists(self.conn_manager, obj)
        return {
            "success": True,
            "data": res,
        }


def test_post_response_useful_route(mock_context):
    """Test post_response when the route is useful."""

    cache = get_cache()  # Creates a new cache
    assert cache.routes.routes == {}
    for i in range(25):
        with patch("aikido_zen.context.get_current_context", return_value=mock_context):
            mock_context.body[str(i + 1)] = i + 1
            request_handler("post_response", status_code=200)

    # Check that the route was initialized and updated
    route = cache.routes.routes.get("GET:/test/route")
    assert route["hits"] == route["hits_delta_since_sync"] == 25
    assert route["method"] == "GET"
    assert route["path"] == "/test/route"

    # Test only updates on first 20 hits
    body_props = route["apispec"]["body"]["schema"]["properties"]
    assert body_props == {
        "1": {"type": "number"},
        "2": {"type": "number", "optional": True},
        "3": {"type": "number", "optional": True},
        "4": {"type": "number", "optional": True},
        "5": {"type": "number", "optional": True},
        "6": {"type": "number", "optional": True},
        "7": {"type": "number", "optional": True},
        "8": {"type": "number", "optional": True},
        "9": {"type": "number", "optional": True},
        "10": {"type": "number", "optional": True},
        "11": {"type": "number", "optional": True},
        "12": {"type": "number", "optional": True},
        "13": {"type": "number", "optional": True},
        "14": {"type": "number", "optional": True},
        "15": {"type": "number", "optional": True},
        "16": {"type": "number", "optional": True},
        "17": {"type": "number", "optional": True},
        "18": {"type": "number", "optional": True},
        "19": {"type": "number", "optional": True},
        "20": {"type": "number", "optional": True},
    }


@patch("aikido_zen.background_process.get_comms")
def test_post_response_not_useful_route(mock_get_comms, mock_context):
    """Test post_response when the route is not useful."""
    comms = MagicMock()
    mock_get_comms.return_value = comms

    cache = ThreadCache()  # Creates a new cache
    assert cache.routes.routes == {}

    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        request_handler("post_response", status_code=500)

    assert cache.routes.routes == {}
    comms.send_data_to_bg_process.assert_not_called()


@patch("aikido_zen.background_process.get_comms")
def test_post_response_no_context(mock_get_comms):
    """Test post_response when there is no context."""
    comms = MagicMock()
    mock_get_comms.return_value = comms

    cache = ThreadCache()  # Creates a new cache
    assert cache.routes.routes == {}

    # Simulate no context
    with patch("aikido_zen.context.get_current_context", return_value=None):
        result = request_handler("post_response", status_code=200)

    assert cache.routes.routes == {}
    comms.send_data_to_bg_process.assert_not_called()


# Test firewall lists
def set_context(remote_address, user_agent="", route="/posts/:number"):
    headers = Headers()
    headers.store_header("USER_AGENT", user_agent)
    Context(
        context_obj={
            "remote_address": remote_address,
            "method": "POST",
            "url": "http://localhost:4000",
            "query": {"abc": "def"},
            "headers": headers,
            "body": None,
            "cookies": {},
            "source": "flask",
            "route": route,
            "user": None,
            "executed_middleware": False,
            "parsed_userinput": {},
        }
    ).set_as_current_context()


def create_service_config():
    config = ServiceConfig(
        endpoints=[
            {
                "method": "POST",
                "route": "/posts/:number",
                "graphql": False,
                "allowedIPAddresses": ["1.1.1.1", "2.2.2.2", "3.3.3.3"],
            }
        ],
        last_updated_at=None,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )
    get_cache().config = config
    return config


def patch_firewall_lists(func):
    def wrapper(*args, **kwargs):
        with patch("aikido_zen.background_process.comms.get_comms") as mock_comms:
            comms = MyMockComms()
            mock_comms.return_value = comms

            sig = inspect.signature(func)
            if "attacks" in sig.parameters:
                kwargs["attacks"] = comms.attacks
            if "firewall_lists" in sig.parameters:
                kwargs["firewall_lists"] = comms.firewall_lists

            return func(*args, **kwargs)

    return wrapper


@patch_firewall_lists
def test_blocked_ip(firewall_lists):
    # Arrange
    firewall_lists.set_blocked_ips(
        [
            {
                "source": "test",
                "description": "Blocked for testing",
                "ips": ["192.168.1.1"],
            }
        ]
    )
    set_context("192.168.1.1")
    config = create_service_config()
    config.endpoints[0]["allowedIPAddresses"] = []  # Clear allowed ips for endpoint

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "Your IP address is blocked due to Blocked for testing (Your IP: 192.168.1.1)",
        403,
    )


@patch_firewall_lists
def test_allowed_ip(firewall_lists):
    # Arrange
    set_context("1.1.1.1")
    firewall_lists.set_blocked_ips(
        [
            {
                "source": "test",
                "description": "Blocked for testing",
                "ips": ["192.168.1.1"],
            }
        ]
    )

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result is None


def test_invalid_context():
    # Arrange
    create_service_config()

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result is None


@patch_firewall_lists
def test_not_allowed_ip(firewall_lists):
    # Arrange
    set_context("192.168.1.3")
    create_service_config()
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    firewall_lists.set_blocked_ips(blocked_ips)

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "Your IP address is not allowed to access this resource. (Your IP: 192.168.1.3)",
        403,
    )


@patch_firewall_lists
def test_ip_allowed_by_endpoint(firewall_lists):
    # Arrange
    set_context("2.2.2.2")  # This IP is in the allowed list
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    firewall_lists.set_blocked_ips(blocked_ips)
    create_service_config()

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result is None  # Should be allowed since it's in the allowed list


@patch_firewall_lists
def test_ip_not_allowed_by_endpoint(firewall_lists):
    # Arrange
    set_context("4.4.4.4")  # Not in the allowed list
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    firewall_lists.set_blocked_ips(blocked_ips)
    config = create_service_config()

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "Your IP address is not allowed to access this resource. (Your IP: 4.4.4.4)",
        403,
    )


@patch_firewall_lists
def test_first_checks_resource_blocked(firewall_lists):
    # Arrange
    set_context("192.168.1.1")  # This IP is blocked
    create_service_config()
    blocked_ips = [
        {
            "source": "test",
            "description": "Blocked for testing",
            "ips": ["192.168.1.1", "192.168.1.2"],
        }
    ]
    firewall_lists.set_blocked_ips(blocked_ips)

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "Your IP address is not allowed to access this resource. (Your IP: 192.168.1.1)",
        403,
    )


@patch_firewall_lists
def test_allowed_for_endpoint_but_blocked(firewall_lists):
    # Arrange
    set_context("1.1.1.1")  # This IP is blocked
    create_service_config()
    blocked_ips = [
        {
            "source": "test",
            "description": "Blocked for testing",
            "ips": ["192.168.1.1", "192.168.1.2", "1.1.1.0/24"],
        }
    ]
    firewall_lists.set_blocked_ips(blocked_ips)

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "Your IP address is blocked due to Blocked for testing (Your IP: 1.1.1.1)",
        403,
    )


@patch_firewall_lists
def test_allowed_for_endpoint_but_not_in_allowlist_and_blocked(firewall_lists):
    # Arrange
    set_context("1.1.1.1")  # This IP is blocked
    create_service_config()
    firewall_lists.set_blocked_ips(
        [
            {
                "source": "test",
                "description": "Blocked for testing",
                "ips": ["192.168.1.1", "192.168.1.2", "1.1.1.0/24"],
            }
        ]
    )
    firewall_lists.set_allowed_ips(
        [
            {
                "source": "test",
                "description": "Allowed ranges",
                "ips": ["4.4.4.0/24"],
            }
        ]
    )

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "Your IP address is not allowed. (Your IP: 1.1.1.1)",
        403,
    )


@patch_firewall_lists
def test_allowed_for_endpoint_but_not_in_allowlist_not_blocked(firewall_lists):
    # Arrange
    set_context("1.1.1.1")  # This IP is blocked
    create_service_config()
    firewall_lists.set_allowed_ips(
        [
            {
                "source": "test",
                "description": "Allowed ranges",
                "ips": ["4.4.4.0/24"],
            }
        ]
    )

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "Your IP address is not allowed. (Your IP: 1.1.1.1)",
        403,
    )


@patch_firewall_lists
def test_allowed_for_endpoint_and_in_allowlist(firewall_lists):
    # Arrange
    set_context("1.1.1.1")  # This IP is blocked
    create_service_config()
    firewall_lists.set_allowed_ips(
        [
            {
                "source": "test",
                "description": "Allowed ranges",
                "ips": ["1.1.1.0/24"],
            }
        ]
    )

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result is None


@patch_firewall_lists
def test_allowed_for_endpoint_in_allowlist_but_blocked(firewall_lists):
    # Arrange
    set_context("1.1.1.1")  # This IP is blocked
    create_service_config()
    firewall_lists.set_blocked_ips(
        [
            {
                "source": "test",
                "description": "Blocked for testing",
                "ips": ["192.168.1.1", "192.168.1.2", "1.1.1.0/24"],
            }
        ]
    )
    firewall_lists.set_allowed_ips(
        [
            {
                "source": "test",
                "description": "Allowed ranges",
                "ips": ["1.1.1.0/24"],
            }
        ]
    )

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "Your IP address is blocked due to Blocked for testing (Your IP: 1.1.1.1)",
        403,
    )


@patch_firewall_lists
def test_allowed_for_endpoint_and_in_allowlist_but_is_bot(firewall_lists):
    # Arrange
    set_context("1.1.1.1", "Test_be bot")
    create_service_config()
    firewall_lists.set_blocked_user_agents("test_ua|test_be")

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "You are not allowed to access this resource because you have been identified as a bot.",
        403,
    )


@patch_firewall_lists
def test_allowed_for_endpoint_and_in_allowlist_but_is_bot_2(firewall_lists):
    # Arrange
    set_context(
        "1.1.1.1",
        "Mozilla/5.0 (compatible; Bytespider/1.0; +http://bytespider.com/bot.html)",
    )
    create_service_config()
    firewall_lists.set_blocked_user_agents(
        "AI2Bot|Applebot-Extended|Bytespider|CCBot|ClaudeBot|cohere-training-data-crawler|Diffbot|Google-Extended|GPTBot|Kangaroo Bot|meta-externalagent|anthropic-ai|omgili|PanguBot|Webzio-Extended|Timpibot|img2dataset|ImagesiftBot|archive.org_bot"
    )

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result == (
        "You are not allowed to access this resource because you have been identified as a bot.",
        403,
    )

    set_context("1.1.1.1", "Mozilla/5.0 (compatible; GPTBot/1.0;")

    result = request_handler("pre_response")

    # Assert
    assert result == (
        "You are not allowed to access this resource because you have been identified as a bot.",
        403,
    )


@patch_firewall_lists
def test_allowed_for_endpoint_and_in_allowlist_bots_are_set_but_is_not_bot(
    firewall_lists,
):
    # Arrange
    set_context("1.1.1.1", "Test_u4 bot")
    create_service_config()
    firewall_lists.set_blocked_user_agents("test_ua|test_be")

    # Act
    result = request_handler("pre_response")

    # Assert
    assert result is None


"""
config.set_blocked_ips(
        [
            {
                "source": "geoip",
                "description": "description",
                "ips": [
                    "1.2.3.4",
                    "192.168.2.1/24",
                    "fd00:1234:5678:9abc::1",
                    "fd00:3234:5678:9abc::1/64",
                    "5.6.7.8/32",
                ],
            }
        ]
    )

    assert config.is_blocked_ip("fd00:3234:5678:9abc::1") is "description"
    assert config.is_blocked_ip("fd00:3234:5678:9abc::2") is "description"
    assert config.is_blocked_ip("5.6.7.8") is "description"
    assert config.is_blocked_ip("1.2") is False
"""


@patch_firewall_lists
def test_multiple_blocked(firewall_lists):
    # Arrange
    blocked_ips = [
        {
            "source": "geoip",
            "description": "description",
            "ips": [
                "1.2.3.4",
                "192.168.2.1/24",
                "fd00:1234:5678:9abc::1",
                "fd00:3234:5678:9abc::1/64",
                "5.6.7.8/32",
            ],
        }
    ]
    firewall_lists.set_blocked_ips(blocked_ips)

    set_context("1.2.3.4")
    assert request_handler("pre_response")[0].startswith("Your IP address is blocked")
    set_context("192.168.2.2")
    assert request_handler("pre_response")[0].startswith("Your IP address is blocked")
    set_context("fd00:1234:5678:9abc::1")
    assert request_handler("pre_response")[0].startswith("Your IP address is blocked")
    set_context("fd00:3234:5678:9abc::1")
    assert request_handler("pre_response")[0].startswith("Your IP address is blocked")
    set_context("fd00:3234:5678:9abc::2")
    assert request_handler("pre_response")[0].startswith("Your IP address is blocked")
    set_context("5.6.7.8")
    assert request_handler("pre_response")[0].startswith("Your IP address is blocked")

    set_context("2.3.4.5")
    assert request_handler("pre_response") is None
    set_context("1.2")
    assert request_handler("pre_response") is None
    set_context("fd00:1234:5678:9abc::2")
    assert request_handler("pre_response") is None


@patch_firewall_lists
def test_attack_wave_detection_in_post_response(firewall_lists):
    """Test attack wave detection happens in post_response stage"""
    set_context("1.1.1.1", route="/.env")
    create_service_config()

    # Reset attack wave detector store for clean test
    from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store

    detector = attack_wave_detector_store._get_detector()
    detector.suspicious_requests_map.clear()
    detector.sent_events_map.clear()

    # Reset stats
    get_cache().stats.clear()

    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 0,
        "blocked": 0,
    }

    # Call request_handler 15 times in post_response to trigger attack wave detection
    for i in range(15):
        request_handler("post_response", status_code=200)

    # The attack wave should be detected
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 1,
        "blocked": 0,
    }

    # now try again (should not be possible due to cooldown window)
    for i in range(15):
        request_handler("post_response", status_code=200)

    # Should still be 1 because of cooldown
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 1,
        "blocked": 0,
    }

    # now try with another IP
    set_context("4.4.4.4", route="/.htaccess")
    for i in range(15):
        request_handler("post_response", status_code=200)

    # Should now be 2 (one for each IP)
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 2,
        "blocked": 0,
    }


@patch_firewall_lists
def test_attack_wave_detection_threshold_not_reached(firewall_lists):
    """Test attack wave detection when threshold is not reached"""
    set_context("2.2.2.2", route="/test")
    create_service_config()

    # Reset attack wave detector store for clean test
    from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store

    detector = attack_wave_detector_store._get_detector()
    detector.suspicious_requests_map.clear()
    detector.sent_events_map.clear()

    # Reset stats
    get_cache().stats.clear()

    # Call request_handler 14 times (below threshold of 15)
    for i in range(14):
        request_handler("post_response", status_code=200)

    # No attack wave should be detected
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 0,
        "blocked": 0,
    }


@patch_firewall_lists
def test_attack_wave_detection_with_cooldown(firewall_lists):
    """Test attack wave detection respects cooldown period"""
    set_context("3.3.3.3", route="/.env")
    create_service_config()

    # Reset attack wave detector store for clean test
    from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store

    detector = attack_wave_detector_store._get_detector()
    detector.suspicious_requests_map.clear()
    detector.sent_events_map.clear()

    # Reset stats
    get_cache().stats.clear()

    # Trigger first attack wave
    for i in range(15):
        request_handler("post_response", status_code=200)

    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 1,
        "blocked": 0,
    }

    # Try to trigger another attack wave immediately (should be blocked by cooldown)
    for i in range(15):
        request_handler("post_response", status_code=200)

    # Should still be 1 due to cooldown
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 1,
        "blocked": 0,
    }


@patch_firewall_lists
def test_attack_wave_detection_no_context(firewall_lists):
    """Test attack wave detection when there is no context"""
    create_service_config()

    # Reset stats
    get_cache().stats.clear()

    # Call request_handler without context
    with patch("aikido_zen.context.get_current_context", return_value=None):
        request_handler("post_response", status_code=200)

    # No attack wave should be detected
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 0,
        "blocked": 0,
    }


@patch_firewall_lists
def test_attack_wave_detection_with_different_routes(firewall_lists):
    """Test attack wave detection with different routes"""
    create_service_config()

    # Reset attack wave detector store for clean test
    from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store

    detector = attack_wave_detector_store._get_detector()
    detector.suspicious_requests_map.clear()
    detector.sent_events_map.clear()

    # Reset stats
    get_cache().stats.clear()

    # Test with different suspicious routes (only use routes that are actually suspicious)
    suspicious_routes = ["/.env", "/.git/config", "/.htaccess"]

    for route in suspicious_routes:
        set_context("5.5.5.5", route=route)
        for i in range(5):  # 5 requests per route to reach threshold
            request_handler("post_response", status_code=200)

    # Should have 15 total requests (5 * 3 routes) which should trigger attack wave
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 1,
        "blocked": 0,
    }


@patch_firewall_lists
def test_attack_wave_detection_with_null_ip(firewall_lists):
    """Test attack wave detection with null/empty IP"""
    set_context("", route="/test")  # Empty IP
    create_service_config()

    # Reset stats
    get_cache().stats.clear()

    # Call request_handler multiple times with empty IP
    for i in range(20):
        request_handler("post_response", status_code=200)

    # No attack wave should be detected for null IP
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 0,
        "blocked": 0,
    }


@patch_firewall_lists
def test_attack_wave_detection_post_response_only(firewall_lists):
    """Test that attack wave detection only happens in post_response stage"""
    set_context("6.6.6.6", route="/.env")
    create_service_config()

    # Reset attack wave detector store for clean test
    from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store

    detector = attack_wave_detector_store._get_detector()
    detector.suspicious_requests_map.clear()
    detector.sent_events_map.clear()

    # Reset stats
    get_cache().stats.clear()

    # Call pre_response multiple times - should not trigger attack wave detection
    for i in range(20):
        request_handler("pre_response")

    # No attack wave should be detected in pre_response
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 0,
        "blocked": 0,
    }

    # Now call post_response to actually trigger detection
    for i in range(15):
        request_handler("post_response", status_code=200)

    # Attack wave should now be detected
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 1,
        "blocked": 0,
    }


@patch_firewall_lists
def test_attack_wave_detection_multiple_ips(firewall_lists):
    """Test attack wave detection with multiple different IPs"""
    create_service_config()

    # Reset attack wave detector store for clean test
    from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store

    detector = attack_wave_detector_store._get_detector()
    detector.suspicious_requests_map.clear()
    detector.sent_events_map.clear()

    # Reset stats
    get_cache().stats.clear()

    # Test with multiple IPs, each making some requests (using suspicious route)
    ips = ["8.8.8.8", "9.9.9.9", "10.10.10.10"]

    for ip in ips:
        set_context(ip, route="/.env")
        for i in range(15):  # 15 requests per IP (threshold)
            request_handler("post_response", status_code=200)

    # Should have 45 total requests (15 * 3 IPs) which should trigger attack wave for each IP
    assert get_cache().stats.get_record()["requests"]["attackWaves"] == {
        "total": 3,  # One attack wave per IP
        "blocked": 0,
    }


@patch_firewall_lists
def test_attack_wave_samples_structure(firewall_lists):
    """Test that attack wave samples contain correct structure with method and URL"""
    set_context("11.11.11.11", route="/.env")
    create_service_config()

    # Reset attack wave detector store for clean test
    from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store

    detector = attack_wave_detector_store._get_detector()
    detector.suspicious_requests_map.clear()
    detector.sent_events_map.clear()

    # Reset stats
    get_cache().stats.clear()

    # Trigger attack wave detection by calling the detector directly
    from aikido_zen.context import get_current_context

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        for i in range(15):
            context = get_current_context()
            detector.is_attack_wave(context)

    # Get the samples that were stored for this IP
    samples = detector.get_samples_for_ip("11.11.11.11")

    # Verify samples structure - should have only 1 unique sample since all requests are identical
    assert len(samples) == 1  # Only 1 unique sample despite 15 identical requests

    # Verify each sample has correct structure (method and url only)
    for sample in samples:
        assert sample["method"] == "POST"
        assert sample["url"] == "http://localhost:4000"  # Full URL from context


@patch_firewall_lists
def test_attack_wave_samples_json_format(firewall_lists):
    """Test that attack wave event contains JSON stringified samples"""
    set_context("12.12.12.12", route="/.git/config")
    create_service_config()

    # Reset attack wave detector store for clean test
    from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store

    detector = attack_wave_detector_store._get_detector()
    detector.suspicious_requests_map.clear()
    detector.sent_events_map.clear()

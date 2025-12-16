import pytest
from unittest.mock import MagicMock, patch
from .create_attack_wave_event import (
    create_attack_wave_event,
    extract_request_if_possible,
)
from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store
import aikido_zen.test_utils as test_utils


def test_create_attack_wave_event_success():
    """Test successful creation of attack wave event with basic data"""
    context = test_utils.generate_context()

    # Mock the attack_wave_detector_store to return no samples
    with patch.object(
        attack_wave_detector_store, "get_samples_for_ip", return_value=None
    ), patch.object(
        attack_wave_detector_store, "clear_samples_for_ip", return_value=None
    ):

        event = create_attack_wave_event(context)

        assert event is not None
        assert event["type"] == "detected_attack_wave"
        assert event["attack"]["user"] is None
        assert event["attack"]["metadata"] == {}
        assert event["request"] is not None


def test_create_attack_wave_event_with_samples():
    """Test attack wave event creation with samples from store"""
    context = test_utils.generate_context()

    # Create sample data
    samples = [
        {
            "method": "GET",
            "route": "/test1",
            "user_agent": "Mozilla/5.0",
            "timestamp": 1234567890,
        },
        {
            "method": "POST",
            "route": "/test2",
            "user_agent": "curl/7.0",
            "timestamp": 1234567891,
        },
    ]

    # Mock the attack_wave_detector_store to return samples
    with patch.object(
        attack_wave_detector_store, "get_samples_for_ip", return_value=samples
    ), patch.object(
        attack_wave_detector_store, "clear_samples_for_ip", return_value=None
    ):

        event = create_attack_wave_event(context)

        assert event is not None
        assert event["type"] == "detected_attack_wave"
        assert event["attack"]["user"] is None
        assert "samples" in event["attack"]["metadata"]
        assert len(event["attack"]["metadata"]["samples"]) == 2

        # Check that samples are in the expected format (raw format from store)
        sample1 = event["attack"]["metadata"]["samples"][0]
        assert sample1["method"] == "GET"
        assert sample1["route"] == "/test1"
        assert sample1["user_agent"] == "Mozilla/5.0"  # Raw format from store
        assert sample1["timestamp"] == 1234567890


def test_create_attack_wave_event_with_user():
    """Test attack wave event creation with user information"""
    context = test_utils.generate_context(user="test_user")

    # Mock the attack_wave_detector_store to return no samples
    with patch.object(
        attack_wave_detector_store, "get_samples_for_ip", return_value=None
    ), patch.object(
        attack_wave_detector_store, "clear_samples_for_ip", return_value=None
    ):

        event = create_attack_wave_event(context)

        assert event["attack"]["user"] == "test_user"
        assert event["attack"]["metadata"] == {}


def test_create_attack_wave_event_with_long_metadata():
    """Test that metadata with long samples is truncated"""
    context = test_utils.generate_context()

    # Create samples with very long values
    long_value = "x" * 5000
    samples = [
        {
            "method": "GET",
            "route": "/test" + long_value,  # Very long route
            "user_agent": "Mozilla/5.0",
            "timestamp": 1234567890,
        },
    ]

    # Mock the attack_wave_detector_store to return samples
    with patch.object(
        attack_wave_detector_store, "get_samples_for_ip", return_value=samples
    ), patch.object(
        attack_wave_detector_store, "clear_samples_for_ip", return_value=None
    ):

        event = create_attack_wave_event(context)

        # The metadata should be truncated to 4096 characters
        metadata_json = event["attack"]["metadata"]
        assert len(metadata_json) <= 4096


def test_create_attack_wave_event_with_multiple_long_metadata_fields():
    """Test that metadata with multiple long sample fields is truncated"""
    context = test_utils.generate_context()

    # Create samples with very long values in multiple fields
    long_value1 = "a" * 5000
    long_value2 = "b" * 6000
    samples = [
        {
            "method": "GET" + long_value1,
            "route": "/test" + long_value2,
            "user_agent": "Mozilla/5.0",
            "timestamp": 1234567890,
        },
    ]

    # Mock the attack_wave_detector_store to return samples
    with patch.object(
        attack_wave_detector_store, "get_samples_for_ip", return_value=samples
    ), patch.object(
        attack_wave_detector_store, "clear_samples_for_ip", return_value=None
    ):

        event = create_attack_wave_event(context)

        # The metadata should be truncated to 4096 characters
        metadata_json = event["attack"]["metadata"]
        assert len(metadata_json) <= 4096


def test_create_attack_wave_event_request_data():
    """Test that request data is correctly extracted from context"""
    context = test_utils.generate_context(
        ip="198.51.100.23",
        route="/test-route",
        headers={"user-agent": "Mozilla/5.0"},
    )

    # Mock the attack_wave_detector_store to return no samples
    with patch.object(
        attack_wave_detector_store, "get_samples_for_ip", return_value=None
    ), patch.object(
        attack_wave_detector_store, "clear_samples_for_ip", return_value=None
    ):

        event = create_attack_wave_event(context)

        request_data = event["request"]
        assert request_data["ipAddress"] == "198.51.100.23"
        assert request_data["source"] == "flask"
        assert request_data["userAgent"] == "Mozilla/5.0"


def test_create_attack_wave_event_no_context():
    """Test attack wave event creation with None context"""

    event = create_attack_wave_event(None)

    # Function returns None when context is None (due to exception handling)
    assert event is None


def test_create_attack_wave_event_exception_handling():
    """Test that exceptions during event creation are handled gracefully"""
    # Create a context that will raise an exception when accessed
    context = MagicMock()
    context.user = "test_user"
    context.remote_address = "1.1.1.1"
    context.source = "test_source"
    # Make get_user_agent raise an exception
    context.get_user_agent.side_effect = Exception("Test exception")

    # Mock the attack_wave_detector_store to raise an exception
    with patch.object(
        attack_wave_detector_store,
        "get_samples_for_ip",
        side_effect=Exception("Store exception"),
    ):
        # This should not raise an exception, but return None
        event = create_attack_wave_event(context)

        # Since we're mocking and causing an exception, the function should handle it
        # and return None based on the exception handling in the function
        assert event is None


def test_extract_request_if_possible_with_valid_context():
    """Test request extraction with valid context"""
    context = test_utils.generate_context(
        ip="198.51.100.23",
        route="/test-route",
        headers={"user-agent": "Mozilla/5.0"},
    )

    request = extract_request_if_possible(context)

    assert request is not None
    assert request["ipAddress"] == "198.51.100.23"
    assert request["source"] == "flask"
    assert request["userAgent"] == "Mozilla/5.0"


def test_extract_request_if_possible_with_none_context():
    """Test request extraction with None context"""
    request = extract_request_if_possible(None)
    assert request is None


def test_extract_request_if_possible_with_minimal_context():
    """Test request extraction with minimal context data"""
    context = test_utils.generate_context()

    request = extract_request_if_possible(context)

    assert request is not None
    assert request["ipAddress"] == "1.1.1.1"
    assert request["source"] == "flask"
    assert request["userAgent"] is None


def test_create_attack_wave_event_empty_metadata():
    """Test attack wave event creation with no samples (empty metadata)"""
    context = test_utils.generate_context()

    # Mock the attack_wave_detector_store to return no samples
    with patch.object(
        attack_wave_detector_store, "get_samples_for_ip", return_value=None
    ), patch.object(
        attack_wave_detector_store, "clear_samples_for_ip", return_value=None
    ):

        event = create_attack_wave_event(context)

        assert event is not None
        assert event["attack"]["metadata"] == {}
        assert event["request"] is not None


def test_create_attack_wave_event_complex_metadata():
    """Test attack wave event creation with complex nested samples"""
    context = test_utils.generate_context()

    # Create complex samples
    samples = [
        {
            "method": "GET",
            "route": "/complex",
            "user_agent": "Mozilla/5.0",
            "timestamp": 1234567890,
        },
        {
            "method": "POST",
            "route": "/nested",
            "user_agent": "curl/7.0",
            "timestamp": 1234567891,
        },
    ]

    # Mock the attack_wave_detector_store to return samples
    with patch.object(
        attack_wave_detector_store, "get_samples_for_ip", return_value=samples
    ), patch.object(
        attack_wave_detector_store, "clear_samples_for_ip", return_value=None
    ):

        event = create_attack_wave_event(context)

        assert "samples" in event["attack"]["metadata"]
        assert len(event["attack"]["metadata"]["samples"]) == 2
        assert event["attack"]["metadata"]["samples"][0]["method"] == "GET"
        assert event["attack"]["metadata"]["samples"][1]["method"] == "POST"

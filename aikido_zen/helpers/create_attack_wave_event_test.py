import pytest
from unittest.mock import MagicMock
from .create_attack_wave_event import create_attack_wave_event, extract_request_if_possible
import aikido_zen.test_utils as test_utils


def test_create_attack_wave_event_success():
    """Test successful creation of attack wave event with basic data"""
    metadata = {"test": "value"}
    context = test_utils.generate_context()
    
    event = create_attack_wave_event(context, metadata)
    
    assert event is not None
    assert event["type"] == "detected_attack_wave"
    assert event["attack"]["user"] is None
    assert event["attack"]["metadata"] == metadata
    assert event["request"] is not None


def test_create_attack_wave_event_with_user():
    """Test attack wave event creation with user information"""
    metadata = {"test": "value"}
    context = test_utils.generate_context(user="test_user")
    
    event = create_attack_wave_event(context, metadata)
    
    assert event["attack"]["user"] == "test_user"
    assert event["attack"]["metadata"] == metadata


def test_create_attack_wave_event_with_long_metadata():
    """Test that metadata longer than 4096 characters is truncated"""
    long_metadata = "x" * 5000  # Create metadata longer than 4096 characters
    metadata = {"test": long_metadata}
    context = test_utils.generate_context()
    
    event = create_attack_wave_event(context, metadata)
    
    assert len(event["attack"]["metadata"]["test"]) == 4096
    assert event["attack"]["metadata"]["test"] == long_metadata[:4096]


def test_create_attack_wave_event_with_multiple_long_metadata_fields():
    """Test that multiple metadata fields longer than 4096 characters are truncated"""
    long_value1 = "a" * 5000
    long_value2 = "b" * 6000
    metadata = {
        "field1": long_value1,
        "field2": long_value2,
    }
    context = test_utils.generate_context()
    
    event = create_attack_wave_event(context, metadata)
    
    assert len(event["attack"]["metadata"]["field1"]) == 4096
    assert len(event["attack"]["metadata"]["field2"]) == 4096
    assert event["attack"]["metadata"]["field1"] == long_value1[:4096]
    assert event["attack"]["metadata"]["field2"] == long_value2[:4096]


def test_create_attack_wave_event_request_data():
    """Test that request data is correctly extracted from context"""
    metadata = {"test": "value"}
    context = test_utils.generate_context(
        ip="198.51.100.23",
        route="/test-route",
        headers={"user-agent": "Mozilla/5.0"},
    )
    
    event = create_attack_wave_event(context, metadata)
    
    request_data = event["request"]
    assert request_data["ipAddress"] == "198.51.100.23"
    assert request_data["source"] == "flask"
    assert request_data["userAgent"] == "Mozilla/5.0"


def test_create_attack_wave_event_no_context():
    """Test attack wave event creation with None context"""
    metadata = {"test": "value"}
    
    event = create_attack_wave_event(None, metadata)
    
    assert event["attack"]["user"] is None
    assert event["attack"]["metadata"] == metadata
    assert event["request"] is None


def test_create_attack_wave_event_exception_handling():
    """Test that exceptions during event creation are handled gracefully"""
    # Create a context that will raise an exception when accessed
    context = MagicMock()
    context.user = "test_user"
    context.remote_address = "1.1.1.1"
    context.source = "test_source"
    # Make get_user_agent raise an exception
    context.get_user_agent.side_effect = Exception("Test exception")
    
    metadata = {"test": "value"}
    
    # This should not raise an exception, but return None
    event = create_attack_wave_event(context, metadata)
    
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
    """Test attack wave event creation with empty metadata"""
    metadata = {}
    context = test_utils.generate_context()
    
    event = create_attack_wave_event(context, metadata)
    
    assert event is not None
    assert event["attack"]["metadata"] == {}
    assert event["request"] is not None


def test_create_attack_wave_event_complex_metadata():
    """Test attack wave event creation with complex nested metadata"""
    metadata = {
        "nested": {
            "key1": "value1",
            "key2": "value2"
        },
        "simple": "simple_value",
        "json_string": '[1, 2, 3]',
        "number_string": "42"
    }
    context = test_utils.generate_context()
    
    event = create_attack_wave_event(context, metadata)
    
    assert event["attack"]["metadata"] == metadata
    assert event["attack"]["metadata"]["nested"]["key1"] == "value1"
    assert event["attack"]["metadata"]["json_string"] == '[1, 2, 3]'


def test_create_attack_wave_event_with_special_characters():
    """Test attack wave event creation with special characters in metadata"""
    metadata = {
        "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
        "unicode": "测试🚀",
        "newlines": "line1\nline2\r\nline3"
    }
    context = test_utils.generate_context()
    
    event = create_attack_wave_event(context, metadata)
    
    assert event["attack"]["metadata"]["special_chars"] == "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    assert event["attack"]["metadata"]["unicode"] == "测试🚀"
    assert event["attack"]["metadata"]["newlines"] == "line1\nline2\r\nline3"

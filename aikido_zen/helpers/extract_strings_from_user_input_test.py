import pytest
from unittest.mock import MagicMock, patch
from aikido_zen.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input,
    extract_strings_from_user_input_cached,
)
from collections import OrderedDict, ChainMap


def from_obj(obj):
    return dict(obj)


def test_empty_object_returns_empty_dict():
    assert extract_strings_from_user_input({}) == from_obj({})


def test_extract_query_objects():
    assert extract_strings_from_user_input({"age": {"$gt": "21"}}) == from_obj(
        {"age": ".", "$gt": ".age", "21": ".age.$gt"}
    )
    assert extract_strings_from_user_input({"title": {"$ne": "null"}}) == from_obj(
        {"title": ".", "$ne": ".title", "null": ".title.$ne"}
    )
    assert extract_strings_from_user_input(
        {"age": "whaat", "user_input": ["whaat", "dangerous"]}
    ) == from_obj(
        {
            "user_input": ".",
            "age": ".",
            "['whaat', 'dangerous']": ".user_input",
            "whaat": ".user_input.[0]",
            "dangerous": ".user_input.[1]",
        }
    )


def test_extract_cookie_objects():
    assert extract_strings_from_user_input(
        {"session": "ABC", "session2": "DEF"}
    ) == from_obj(
        {"session2": ".", "session": ".", "ABC": ".session", "DEF": ".session2"}
    )
    assert extract_strings_from_user_input(
        {"session": "ABC", "session2": 1234}
    ) == from_obj({"session2": ".", "session": ".", "ABC": ".session"})


def test_extract_cookie_objects_as_chainmap():
    assert extract_strings_from_user_input(
        ChainMap({"session": "ABC"}, {"session2": "DEF"})
    ) == from_obj(
        {"session2": ".", "session": ".", "ABC": ".session", "DEF": ".session2"}
    )
    assert extract_strings_from_user_input(
        ChainMap({"session": "ABC"}, {"session2": 1234})
    ) == from_obj({"session2": ".", "session": ".", "ABC": ".session"})


def test_extract_cookie_objects_from_ordereddict():
    assert extract_strings_from_user_input(
        OrderedDict({"session": "ABC", "session2": "DEF"})
    ) == from_obj(
        {"session2": ".", "session": ".", "ABC": ".session", "DEF": ".session2"}
    )
    assert extract_strings_from_user_input(
        OrderedDict({"session": "ABC", "session2": 1234})
    ) == from_obj({"session2": ".", "session": ".", "ABC": ".session"})


def test_extract_header_objects():
    assert extract_strings_from_user_input(
        {"Content-Type": "application/json"}
    ) == from_obj({"Content-Type": ".", "application/json": ".Content-Type"})
    assert extract_strings_from_user_input({"Content-Type": 54321}) == from_obj(
        {"Content-Type": "."}
    )
    assert extract_strings_from_user_input(
        {"Content-Type": "application/json", "ExtraHeader": "value"}
    ) == from_obj(
        {
            "Content-Type": ".",
            "application/json": ".Content-Type",
            "ExtraHeader": ".",
            "value": ".ExtraHeader",
        }
    )


def test_extract_body_objects():
    assert extract_strings_from_user_input(
        {"nested": {"nested": {"$ne": None}}}
    ) == from_obj({"nested": ".nested", "$ne": ".nested.nested"})
    assert extract_strings_from_user_input(
        {"age": {"$gt": "21", "$lt": "100"}}
    ) == from_obj(
        {"age": ".", "$lt": ".age", "$gt": ".age", "21": ".age.$gt", "100": ".age.$lt"}
    )


def test_decodes_jwts():
    assert extract_strings_from_user_input(
        {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ"
        }
    ) == from_obj(
        {
            "token": ".",
            "iat": ".token<jwt>",
            "username": ".token<jwt>",
            "sub": ".token<jwt>",
            "1234567890": ".token<jwt>.sub",
            "$ne": ".token<jwt>.username",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ": ".token",
        }
    )


def test_ignores_jwt_issuers():
    """
    {
        "sub": "1234567890",
        "name": "John Doe",
        "iat": 1516239022,
        "iss": "https://example.com"
    }
    """
    assert extract_strings_from_user_input(
        {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJpc3MiOiJodHRwczovL2V4YW1wbGUuY29tIn0.QLC0vl-A11a1WcUPD6vQR2PlUvRMsqpegddfQzPajQM",
        }
    ) == {
        "token": ".",
        "iat": ".token<jwt>",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJpc3MiOiJodHRwczovL2V4YW1wbGUuY29tIn0.QLC0vl-A11a1WcUPD6vQR2PlUvRMsqpegddfQzPajQM": ".token",
        "sub": ".token<jwt>",
        "1234567890": ".token<jwt>.sub",
        "name": ".token<jwt>",
        "John Doe": ".token<jwt>.name",
    }


def test_jwt_as_string():
    assert extract_strings_from_user_input(
        {"header": "/;ping%20localhost;.e30=."}
    ) == from_obj({"header": ".", "/;ping%20localhost;.e30=.": ".header"})


def test_extracts_strings_from_string_array():
    assert extract_strings_from_user_input({"arr": ["1", "2", "3"]}) == from_obj(
        {
            "arr": ".",
            "['1', '2', '3']": ".arr",
            "1": ".arr.[0]",
            "2": ".arr.[1]",
            "3": ".arr.[2]",
        }
    )


def test_extracts_strings_from_mixed_array():
    assert extract_strings_from_user_input(
        {"arr": ["1", 2, True, None, {"test": "test"}]}
    ) == from_obj(
        {
            "arr": ".",
            "1": ".arr.[0]",
            "test": ".arr.[4].test",
            "['1', 2, True, None, {'test': 'test'}]": ".arr",
        }
    )


def test_extracts_strings_from_mixed_array_containing_array():
    assert extract_strings_from_user_input(
        {"arr": ["1", 2, True, None, {"test": ["test123", "test345"]}]}
    ) == from_obj(
        {
            "arr": ".",
            "1": ".arr.[0]",
            "test": ".arr.[4]",
            "test123": ".arr.[4].test.[0]",
            "test345": ".arr.[4].test.[1]",
            "['test123', 'test345']": ".arr.[4].test",
            "['1', 2, True, None, {'test': ['test123', 'test345']}]": ".arr",
        }
    )


# Mocking the dependencies
def mock_extract_strings_from_user_input(obj):
    return {"input1": "value1", "input2": "value2"}


@pytest.fixture
def mock_context():
    """Fixture to create a mock context."""
    context = MagicMock()
    context.parsed_userinput = {}
    return context


def test_extract_strings_from_user_input_cached_no_context(mock_context):
    # Arrange
    obj = "some input object"
    with patch("aikido_zen.context.get_current_context", return_value=None):
        with patch(
            "aikido_zen.helpers.extract_strings_from_user_input.extract_strings_from_user_input",
            side_effect=mock_extract_strings_from_user_input,
        ):
            # Act
            result = extract_strings_from_user_input_cached(obj, "source1")

            # Assert
            assert result == {"input1": "value1", "input2": "value2"}


def test_extract_strings_from_user_input_cached_with_context_no_cache(mock_context):
    # Arrange
    obj = "some input object"
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        with patch(
            "aikido_zen.helpers.extract_strings_from_user_input.extract_strings_from_user_input",
            side_effect=mock_extract_strings_from_user_input,
        ):
            # Act
            result = extract_strings_from_user_input_cached(obj, "source1")

            # Assert
            assert result == {"input1": "value1", "input2": "value2"}
            assert mock_context.parsed_userinput["source1"] == result


def test_extract_strings_from_user_input_cached_with_context_cache_hit(mock_context):
    # Arrange
    obj = "some input object"
    mock_context.parsed_userinput["source1"] = {
        "input1": "cached_value1",
        "input2": "cached_value2",
    }
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        # Act
        result = extract_strings_from_user_input_cached(obj, "source1")

        # Assert
        assert result == {"input1": "cached_value1", "input2": "cached_value2"}
        # Ensure extract_strings_from_user_input is not called
        with patch(
            "aikido_zen.helpers.extract_strings_from_user_input.extract_strings_from_user_input"
        ) as mock_extract:
            extract_strings_from_user_input_cached(obj, "source1")
            mock_extract.assert_not_called()


def test_extract_strings_from_user_input_cached_with_context_cache_update(mock_context):
    # Arrange
    obj = "some input object"
    mock_context.parsed_userinput["source1"] = {}
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        with patch(
            "aikido_zen.helpers.extract_strings_from_user_input.extract_strings_from_user_input",
            side_effect=mock_extract_strings_from_user_input,
        ):
            # Act
            result = extract_strings_from_user_input_cached(obj, "source1")

            # Assert
            assert result == {"input1": "value1", "input2": "value2"}
            assert mock_context.parsed_userinput["source1"] == result


def test_extract_strings_from_user_input_cached_multiple_sources(mock_context):
    # Arrange
    obj = "some input object"
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        with patch(
            "aikido_zen.helpers.extract_strings_from_user_input.extract_strings_from_user_input",
            side_effect=mock_extract_strings_from_user_input,
        ):
            # Act
            result1 = extract_strings_from_user_input_cached(obj, "source1")
            result2 = extract_strings_from_user_input_cached(obj, "source2")

            # Assert
            assert result1 == {"input1": "value1", "input2": "value2"}
            assert result2 == {"input1": "value1", "input2": "value2"}
            assert mock_context.parsed_userinput["source1"] == result1
            assert mock_context.parsed_userinput["source2"] == result2


# To run the tests, use the command: pytest <filename>.py

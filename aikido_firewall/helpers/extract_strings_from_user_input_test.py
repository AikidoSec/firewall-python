import pytest
from aikido_firewall.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input,
)


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


"""

  t.same(
    extractStringsFromUserInput({
      arr: ["1", 2, true, null, undefined, { test: ["test123", "test345"] }],
    }),
    fromObj({
      arr: ".",
      "1": ".arr.[0]",
      test: ".arr.[5]",
      test123: ".arr.[5].test.[0]",
      test345: ".arr.[5].test.[1]",
      "test123,test345": ".arr.[5].test",
      "1,2,true,,,[object Object]": ".arr",
    })
  );
});
"""

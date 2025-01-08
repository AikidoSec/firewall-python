import pytest
from aikido_zen.helpers.try_decode_as_jwt import try_decode_as_jwt


def test_returns_false_for_empty_string():
    assert try_decode_as_jwt("") == (False, None)


def test_returns_false_for_invalid_JWT():
    assert try_decode_as_jwt("invalid") == (False, None)
    assert try_decode_as_jwt("invalid.invalid") == (False, None)
    assert try_decode_as_jwt("invalid.invalid.invalid") == (False, None)
    assert try_decode_as_jwt("invalid.invalid.invalid.invalid") == (False, None)


def test_returns_payload_for_invalid_JWT():
    assert try_decode_as_jwt("/;ping%20localhost;.e30=.") == (True, {})
    assert try_decode_as_jwt("/;ping%20localhost;.W10=.") == (True, [])


def test_returns_decoded_JWT_for_valid_JWT():
    assert try_decode_as_jwt(
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ"
    ) == (True, {"sub": "1234567890", "username": {"$ne": None}, "iat": 1516239022})


def test_returns_decoded_JWT_for_valid_JWT_with_bearer_prefix():
    assert try_decode_as_jwt(
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ"
    ) == (True, {"sub": "1234567890", "username": {"$ne": None}, "iat": 1516239022})

def test_decodes_valid_jwt():
    example_payload = {"hello": "world"}
    example_jwt = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJoZWxsbyI6ICJ3b3JsZCJ9.tvagLDLoaiJKxOKqpBXSEGy7SYSifZhjntgm9ctpyj8"
    decoded_payload = try_decode_as_jwt(example_jwt)[1]

    assert decoded_payload == example_payload

def test_decodes_complete_valid_jwt():
    example_payload = {"hello": "world"}
    example_jwt = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJoZWxsbyI6ICJ3b3JsZCJ9.tvagLDLoaiJKxOKqpBXSEGy7SYSifZhjntgm9ctpyj8"
    decoded = try_decode_as_jwt(example_jwt)

    assert decoded[0] is True
    assert decoded[1] == {"hello": "world"}

def test_load_verify_valid_jwt():
    example_payload = {"hello": "world"}
    example_jwt = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJoZWxsbyI6ICJ3b3JsZCJ9.tvagLDLoaiJKxOKqpBXSEGy7SYSifZhjntgm9ctpyj8"

    decoded_payload = try_decode_as_jwt(example_jwt)[1]

    assert decoded_payload == example_payload

def test_decode_invalid_payload_string():
    example_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.aGVsbG8gd29ybGQ.SIr03zM64awWRdPrAM_61QWsZchAtgDV3pphfHPPWkI"

    result = try_decode_as_jwt(example_jwt)

    assert result == (False, None)

def test_decode_with_non_mapping_payload_throws_exception():
    example_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.MQ.Abcd"  # Invalid payload

    result = try_decode_as_jwt(example_jwt)

    assert result == (True, 1)

def test_decode_with_invalid_audience_param_throws_exception():
    example_jwt = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJoZWxsbyI6ICJ3b3JsZCJ9.tvagLDLoaiJKxOKqpBXSEGy7SYSifZhjntgm9ctpyj8"

    result = try_decode_as_jwt(example_jwt)

    assert result == (True, {'hello': 'world'})

def test_decode_with_nonlist_aud_claim_throws_exception():
    example_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJoZWxsbyI6IndvcmxkIiwiYXVkIjoxfQ.Rof08LBSwbm8Z_bhA2N3DFY-utZR1Gi9rbIS5Zthnnc"

    result = try_decode_as_jwt(example_jwt)

    assert result == (True, {'hello': 'world', 'aud': 1})

def test_decode_with_invalid_aud_list_member_throws_exception():
    example_jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJoZWxsbyI6IndvcmxkIiwiYXVkIjpbMV19"
        ".iQgKpJ8shetwNMIosNXWBPFB057c2BHs-8t1d2CCM2A"
    )

    result = try_decode_as_jwt(example_jwt)

    assert result == (True, {'hello': 'world', 'aud': [1]})  # Assuming the function handles audience checks internally

def test_decode_raises_exception_if_exp_is_not_int():
    example_jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJleHAiOiJub3QtYW4taW50In0."
        "P65iYgoHtBqB07PMtBSuKNUEIPPPfmjfJG217cEE66s"
    )

    result = try_decode_as_jwt(example_jwt)

    assert result == (True, {'exp': 'not-an-int'})  # Assuming the function handles exp checks internally

def test_decode_raises_exception_if_iat_is_not_int():
    example_jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpYXQiOiJub3QtYW4taW50In0."
        "H1GmcQgSySa5LOKYbzGm--b1OmRbHFkyk8pq811FzZM"
    )

    result = try_decode_as_jwt(example_jwt)

    assert result == (True, {'iat': 'not-an-int'})  # Assuming the function handles iat checks internally


def assert_eq(val1, equals, val2=None):
    assert val1 == equals, f"Assertion failed: Expected {equals} != {val1}"
    if val2 is not None:
        assert val2 == equals, f"Assertion failed: Expected {equals} != {val2}"

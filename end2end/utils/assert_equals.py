def assert_eq(val1, equals=None, val2=None, inside=None):
    if inside:
        assert val1 in inside, f"Assertion failed: Expected {val1} in {inside}"
    else:
        assert val1 == equals, f"Assertion failed: Expected {equals} != {val1}"
    if val2 is not None:
        # Pass along val2 as a val1
        assert_eq(val2, equals=equals, inside=inside)

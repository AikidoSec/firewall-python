import pytest
from aikido_firewall.helpers.is_plain_object import is_plain_object


def test_is_plain_object_true():
    assert is_plain_object({}) == True
    assert is_plain_object({"foo": "bar"}) == True


def test_is_plain_object_false():
    class Foo:
        def __init__(self):
            self.abc = {}

    foo_instance = Foo()

    assert is_plain_object("/foo/") == False
    assert is_plain_object(lambda: None) == False
    assert is_plain_object(1) == False
    assert is_plain_object(["foo", "bar"]) == False
    assert is_plain_object([]) == False
    assert is_plain_object(foo_instance) == False
    assert is_plain_object(None) == False


def test_is_plain_object_modified_prototype():
    class CustomConstructor:
        pass

    CustomConstructor.prototype = list

    instance = CustomConstructor()

    assert is_plain_object(instance) == False

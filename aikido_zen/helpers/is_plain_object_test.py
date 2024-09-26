import pytest
from aikido_zen.helpers.is_plain_object import is_plain_object
from collections import defaultdict, OrderedDict, ChainMap


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


def test_is_plain_object_mapping_types():
    fruit_count = defaultdict(int)
    fruit_count["apple"] += 1
    fruit_count["banana"] += 2
    assert is_plain_object(fruit_count) == True

    ordered_dict = OrderedDict()
    ordered_dict["first"] = 1
    ordered_dict["second"] = 2
    ordered_dict["third"] = 3
    assert is_plain_object(ordered_dict) == True

    dict1 = {"a": 1, "b": 2}
    dict2 = {"b": 3, "c": 4}
    chain_map = ChainMap(dict1, dict2)
    assert is_plain_object(chain_map) == True

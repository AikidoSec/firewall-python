import pytest
from aikido_zen.helpers.is_mapping import is_mapping
from collections import defaultdict, OrderedDict, ChainMap


def test_is_mapping_true():
    assert is_mapping({}) == True
    assert is_mapping({"foo": "bar"}) == True


def test_is_mapping_false():
    class Foo:
        def __init__(self):
            self.abc = {}

    foo_instance = Foo()

    assert is_mapping("/foo/") == False
    assert is_mapping(lambda: None) == False
    assert is_mapping(1) == False
    assert is_mapping(["foo", "bar"]) == False
    assert is_mapping([]) == False
    assert is_mapping(foo_instance) == False
    assert is_mapping(None) == False


def test_is_mapping_modified_prototype():
    class CustomConstructor:
        pass

    CustomConstructor.prototype = list

    instance = CustomConstructor()

    assert is_mapping(instance) == False


def test_is_mapping_mapping_types():
    fruit_count = defaultdict(int)
    fruit_count["apple"] += 1
    fruit_count["banana"] += 2
    assert is_mapping(fruit_count) == True

    ordered_dict = OrderedDict()
    ordered_dict["first"] = 1
    ordered_dict["second"] = 2
    ordered_dict["third"] = 3
    assert is_mapping(ordered_dict) == True

    dict1 = {"a": 1, "b": 2}
    dict2 = {"b": 3, "c": 4}
    chain_map = ChainMap(dict1, dict2)
    assert is_mapping(chain_map) == True

import pytest
import time
from .lru_cache import LRUCache


def test_lru_cache_creation():
    map = LRUCache(5, 1000)
    assert map.size == 0, "Size should be 0 initially"


def test_lru_cache_invalid_constructor_args():
    with pytest.raises(ValueError, match="Invalid max value"):
        LRUCache(-1, 1000)
    with pytest.raises(ValueError, match="Invalid ttl value"):
        LRUCache(100, -1)


def test_lru_cache_set_and_get_methods():
    map = LRUCache(5, 1000)

    map.set("key1", "value1")
    assert map.get("key1") == "value1", "Value should be retrieved correctly"

    map.set("key2", "value2")
    assert map.get("key2") == "value2", "Value should be retrieved correctly"

    assert map.size == 2, "Size should be 2 after adding two items"


def test_lru_cache_eviction_policy():
    map = LRUCache(2, 1000)

    map.set(1, "value1")
    map.set(2, "value2")
    assert map.size == 2, "Size should be 2 after adding two items"

    map.set(3, "value3")
    assert map.size == 2, "Size should be 2 after adding third item"
    assert map.get(1) is None, "First item should be evicted"
    assert map.get(2) == "value2", "Second item should still be present"
    assert map.get(3) == "value3", "Third item should be present"


def test_lru_cache_ttl_expiration():
    map = LRUCache(5, 100)

    map.set("key1", "value1")
    assert map.get("key1") == "value1", "Value should be retrieved correctly"

    # Wait for TTL to expire
    time.sleep(0.15)

    assert map.get("key1") is None, "Value should be None after TTL expiration"
    assert map.size == 0, "Size should be 0 after TTL expiration"


def test_lru_cache_clear_method():
    map = LRUCache(5, 1000)

    map.set("key1", "value1")
    map.set("key2", "value2")
    assert map.size == 2, "Size should be 2 after adding two items"

    map.clear()
    assert map.size == 0, "Size should be 0 after clearing"
    assert map.get("key1") is None, "Value should be None after clearing"
    assert map.get("key2") is None, "Value should be None after clearing"


def test_lru_cache_delete_method():
    map = LRUCache(5, 1000)

    map.set("key1", "value1")
    map.set("key2", "value2")
    assert map.size == 2, "Size should be 2 after adding two items"

    map.delete("key1")
    assert map.size == 1, "Size should be 1 after deleting one item"
    assert map.get("key1") is None, "Value should be None after deletion"
    assert (
        map.get("key2") == "value2"
    ), "Value should be retrieved correctly for remaining item"


def test_lru_cache_keys_method():
    map = LRUCache(5, 1000)

    map.set("key1", "value1")
    map.set("key2", "value2")
    map.set("key3", "value3")

    keys = map.keys()
    assert keys == ["key1", "key2", "key3"], "Keys should be retrieved correctly"

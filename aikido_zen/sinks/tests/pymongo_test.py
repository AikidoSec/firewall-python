import pytest
from unittest.mock import patch
import aikido_zen.sinks.pymongo
from aikido_zen.background_process.comms import reset_comms
import pymongo.errors as mongo_errs
from collections import defaultdict, OrderedDict, ChainMap


@pytest.fixture
def db():
    from pymongo import MongoClient

    client = MongoClient("mongodb://admin:password@127.0.0.1:27017")
    return client["my_database"]


def test_replace_one(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter, repl = {"dog_name": "test"}, {"dog_name": "dog2", "pswd": "pswd"}
        dogs.replace_one(filter, repl)

        # call 0 = filter, call 1 = replacement
        called_with = mock_run_vulnerability_scan.call_args_list[0][1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.replace_one"
        assert called_with["kind"] == "nosql_injection"


def test_replace_one_with_chainmap(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        repl = {"dog_name": "dog2", "pswd": "pswd"}
        filter = ChainMap({"dog_name": "test"}, {})
        dogs.replace_one(filter, repl)

        # call 0 = filter, call 1 = replacement
        called_with = mock_run_vulnerability_scan.call_args_list[0][1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.replace_one"
        assert called_with["kind"] == "nosql_injection"


def test_update_one(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter, update = {"dog_name": "test"}, {"pswd": "pswd"}
        dogs.update_one(filter, {"$set": update})

        # call 0 = filter, call 1 = update doc
        called_with = mock_run_vulnerability_scan.call_args_list[0][1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.update_one"
        assert called_with["kind"] == "nosql_injection"


def test_update_many(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter, update = {"dog_name": "test"}, {"pswd": "pswd"}
        dogs.update_many(filter, {"$set": update})

        # call 0 = filter, call 1 = update doc
        called_with = mock_run_vulnerability_scan.call_args_list[0][1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.update_many"
        assert called_with["kind"] == "nosql_injection"


def test_delete_one(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter = {"dog_name": "test"}
        dogs.delete_one(filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.delete_one"
        assert called_with["kind"] == "nosql_injection"


def test_delete_many(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter = {"dog_name": "test"}
        dogs.delete_many(filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.delete_many"
        assert called_with["kind"] == "nosql_injection"


def test_find_one(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.find_one(_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_count_documents(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.count_documents(_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.count_documents"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_find_one_and_delete(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.find_one_and_delete(_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_one_and_delete"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_find_one_and_replace(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.find_one_and_replace(filter=_filter, replacement={"dog_name": "test2"})

        # call 0 = filter, call 1 = replacement
        called_with = mock_run_vulnerability_scan.call_args_list[0][1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_one_and_replace"
        assert called_with["kind"] == "nosql_injection"


def test_find_one_and_update(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.find_one_and_update(_filter, {"$set": {"dog_name": "test2"}})

        # call 0 = filter, call 1 = update doc
        called_with = mock_run_vulnerability_scan.call_args_list[0][1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_one_and_update"
        assert called_with["kind"] == "nosql_injection"


def test_find_empty(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.find()
        mock_run_vulnerability_scan.assert_not_called()


def test_find_not_empty(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.find(_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_find_raw_batches(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.find_raw_batches(_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_raw_batches"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_distinct(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.distinct("pswd", _filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.distinct"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_distinct_kwargs(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.distinct(key="pswd", filter=_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.distinct"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_distinct_empty(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.distinct("pswd")

        mock_run_vulnerability_scan.assert_not_called()


def test_aggregate(db):
    pipeline = [
        {
            "$group": {
                "_id": "$item",
                "total_quantity": {"$sum": "$quantity"},
                "average_price": {"$avg": "$price"},
            }
        },
        {"$sort": {"total_quantity": -1}},  # Sort by total_quantity in descending order
    ]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.aggregate(pipeline)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert called_with["op"] == "pymongo.collection.Collection.aggregate"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_aggregate_key(db):
    pipeline = [
        {
            "$group": {
                "_id": "$item",
                "total_quantity": {"$sum": "$quantity"},
                "average_price": {"$avg": "$price"},
            }
        },
        {"$sort": {"total_quantity": -1}},  # Sort by total_quantity in descending order
    ]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.aggregate(pipeline=pipeline)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert called_with["op"] == "pymongo.collection.Collection.aggregate"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_aggregate_raw_batches_key(db):
    pipeline = [
        {
            "$group": {
                "_id": "$item",
                "total_quantity": {"$sum": "$quantity"},
                "average_price": {"$avg": "$price"},
            }
        },
        {"$sort": {"total_quantity": -1}},  # Sort by total_quantity in descending order
    ]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.aggregate_raw_batches(pipeline=pipeline)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert (
            called_with["op"] == "pymongo.collection.Collection.aggregate_raw_batches"
        )
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_aggregate_raw_batches(db):
    pipeline = [
        {
            "$group": {
                "_id": "$item",
                "total_quantity": {"$sum": "$quantity"},
                "average_price": {"$avg": "$price"},
            }
        },
        {"$sort": {"total_quantity": -1}},  # Sort by total_quantity in descending order
    ]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.aggregate_raw_batches(pipeline)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert (
            called_with["op"] == "pymongo.collection.Collection.aggregate_raw_batches"
        )
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_watch(db):
    pipeline = [
        {
            "$group": {
                "_id": "$item",
                "total_quantity": {"$sum": "$quantity"},
                "average_price": {"$avg": "$price"},
            }
        },
        {"$sort": {"total_quantity": -1}},  # Sort by total_quantity in descending order
    ]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        with pytest.raises(mongo_errs.OperationFailure):
            dogs.watch(pipeline)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert called_with["op"] == "pymongo.collection.Collection.watch"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_watch_key(db):
    pipeline = [
        {
            "$group": {
                "_id": "$item",
                "total_quantity": {"$sum": "$quantity"},
                "average_price": {"$avg": "$price"},
            }
        },
        {"$sort": {"total_quantity": -1}},  # Sort by total_quantity in descending order
    ]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        with pytest.raises(mongo_errs.OperationFailure):
            dogs.watch(pipeline=pipeline)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert called_with["op"] == "pymongo.collection.Collection.watch"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_bulk_write(db):
    from pymongo import InsertOne, UpdateOne, DeleteOne

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        requests = [
            InsertOne({"dog_name": "Buddy2", "age": 3}),
            InsertOne({"dog_name": "Max3"}),
            UpdateOne({"dog_name": "Buddy1"}, {"$set": {"age": 0}}),
            DeleteOne({"dog_name": "Max3"}),
            InsertOne({"dog_name": "Bella4"}),
        ]
        try:
            dogs.bulk_write(requests)
        except Exception:
            pass
        calls = mock_run_vulnerability_scan.call_args_list

        # call 0: UpdateOne filter
        called_with1 = calls[0][1]
        assert called_with1["args"][0] == {"dog_name": "Buddy1"}
        assert called_with1["op"] == "pymongo.collection.Collection.bulk_write"
        assert called_with1["kind"] == "nosql_injection"

        # call 1: UpdateOne update doc (the fix)
        called_with_update = calls[1][1]
        assert called_with_update["args"][0] == {"$set": {"age": 0}}
        assert called_with_update["op"] == "pymongo.collection.Collection.bulk_write"
        assert called_with_update["kind"] == "nosql_injection"

        # call 2: DeleteOne filter
        called_with2 = calls[2][1]
        assert called_with2["args"][0] == {"dog_name": "Max3"}
        assert called_with2["op"] == "pymongo.collection.Collection.bulk_write"
        assert called_with2["kind"] == "nosql_injection"


def test_bulk_write_scans_update_doc(db):
    """Update doc in bulk_write must be scanned (bypass fix)."""
    from pymongo import UpdateOne, UpdateMany

    update_doc = {"$set": {"role": "admin"}}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        try:
            dogs.bulk_write([UpdateOne({"dog_name": "test"}, update_doc)])
        except Exception:
            pass
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert update_doc in scanned_args


def test_bulk_write_scans_update_many_doc(db):
    """UpdateMany doc in bulk_write must be scanned."""
    from pymongo import UpdateMany

    update_doc = {"$set": {"role": "admin"}}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        try:
            dogs.bulk_write([UpdateMany({"dog_name": "test"}, update_doc)])
        except Exception:
            pass
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert update_doc in scanned_args


def test_bulk_write_scans_replace_one_doc(db):
    """ReplaceOne replacement doc in bulk_write must be scanned."""
    from pymongo import ReplaceOne

    replacement = {"dog_name": "hacked", "role": "admin"}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        try:
            dogs.bulk_write([ReplaceOne({"dog_name": "test"}, replacement)])
        except Exception:
            pass
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert replacement in scanned_args


def test_bulk_write_insert_only_does_not_scan(db):
    """InsertOne (no filter) must not trigger a scan."""
    from pymongo import InsertOne

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        try:
            dogs.bulk_write([InsertOne({"dog_name": "buddy"})])
        except Exception:
            pass
        mock_run_vulnerability_scan.assert_not_called()


def test_bulk_write_delete_does_not_scan_doc(db):
    """DeleteOne has no update doc — only its filter is scanned."""
    from pymongo import DeleteOne

    _filter = {"dog_name": "test"}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        try:
            dogs.bulk_write([DeleteOne(_filter)])
        except Exception:
            pass
        calls = mock_run_vulnerability_scan.call_args_list
        assert len(calls) == 1
        assert calls[0][1]["args"][0] == _filter


# --- update_one: update arg (bypass fix) ---


def test_update_one_scans_update_arg(db):
    """update_one must scan the update document, not just the filter."""
    update = {"$set": {"pswd": "hacked"}}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.update_one({"dog_name": "test"}, update)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert update in scanned_args


def test_update_one_scans_update_pipeline(db):
    """update_one with an aggregation pipeline update must be scanned."""
    pipeline_update = [{"$set": {"role": "admin"}}]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.update_one({"dog_name": "test"}, pipeline_update)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert pipeline_update in scanned_args


def test_update_one_scans_update_kwarg(db):
    """update_one with update passed as kwarg must be scanned."""
    update = {"$set": {"pswd": "hacked"}}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.update_one(filter={"dog_name": "test"}, update=update)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert update in scanned_args


def test_update_one_scans_both_filter_and_update(db):
    """update_one must scan both the filter AND the update document."""
    _filter = {"dog_name": "test"}
    update = {"$set": {"pswd": "hacked"}}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.update_one(_filter, update)
        calls = mock_run_vulnerability_scan.call_args_list
        assert len(calls) == 2
        scanned_args = [c[1]["args"][0] for c in calls]
        assert _filter in scanned_args
        assert update in scanned_args


def test_update_one_addfields_bypass(db):
    """Reproduce the exact PoC from the bug report: $addFields in update arg."""
    injected_update = [{"$addFields": {"test": "new fields"}}]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.update_one({"username": "test"}, injected_update)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert injected_update in scanned_args


# --- update_many: update arg ---


def test_update_many_scans_update_arg(db):
    """update_many must scan the update document."""
    update = {"$set": {"role": "admin"}}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.update_many({"dog_name": "test"}, update)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert update in scanned_args


def test_update_many_scans_update_pipeline(db):
    """update_many with aggregation pipeline update must be scanned."""
    pipeline_update = [{"$set": {"role": "admin"}}, {"$unset": "password"}]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.update_many({"dog_name": "test"}, pipeline_update)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert pipeline_update in scanned_args


def test_update_many_scans_both_filter_and_update(db):
    """update_many must scan both filter AND update."""
    _filter = {"dog_name": "test"}
    update = {"$inc": {"age": 1}}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.update_many(_filter, update)
        calls = mock_run_vulnerability_scan.call_args_list
        assert len(calls) == 2
        scanned_args = [c[1]["args"][0] for c in calls]
        assert _filter in scanned_args
        assert update in scanned_args


# --- replace_one: replacement arg ---


def test_replace_one_scans_replacement_arg(db):
    """replace_one must scan the replacement document, not just the filter."""
    replacement = {"dog_name": "hacked", "role": "admin"}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.replace_one({"dog_name": "test"}, replacement)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert replacement in scanned_args


def test_replace_one_scans_replacement_kwarg(db):
    """replace_one with replacement as kwarg must be scanned."""
    replacement = {"dog_name": "hacked"}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.replace_one(filter={"dog_name": "test"}, replacement=replacement)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert replacement in scanned_args


def test_replace_one_scans_both_filter_and_replacement(db):
    """replace_one must scan both filter AND replacement."""
    _filter = {"dog_name": "test"}
    replacement = {"dog_name": "hacked"}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.replace_one(_filter, replacement)
        calls = mock_run_vulnerability_scan.call_args_list
        assert len(calls) == 2
        scanned_args = [c[1]["args"][0] for c in calls]
        assert _filter in scanned_args
        assert replacement in scanned_args


# --- find_one_and_update: update arg ---


def test_find_one_and_update_scans_update_arg(db):
    """find_one_and_update must scan the update document."""
    update = {"$set": {"role": "admin"}}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.find_one_and_update({"dog_name": "test"}, update)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert update in scanned_args


def test_find_one_and_update_scans_update_pipeline(db):
    """find_one_and_update with aggregation pipeline update must be scanned."""
    pipeline_update = [{"$addFields": {"hacked": True}}]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.find_one_and_update({"dog_name": "test"}, pipeline_update)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert pipeline_update in scanned_args


def test_find_one_and_update_scans_both_filter_and_update(db):
    """find_one_and_update must scan both filter AND update."""
    _filter = {"dog_name": "test", "pswd": "pswd"}
    update = {"$set": {"dog_name": "hacked"}}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.find_one_and_update(_filter, update)
        calls = mock_run_vulnerability_scan.call_args_list
        assert len(calls) == 2
        scanned_args = [c[1]["args"][0] for c in calls]
        assert _filter in scanned_args
        assert update in scanned_args


# --- find_one_and_replace: replacement arg ---


def test_find_one_and_replace_scans_replacement_arg(db):
    """find_one_and_replace must scan the replacement document."""
    replacement = {"dog_name": "hacked"}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.find_one_and_replace(filter={"dog_name": "test"}, replacement=replacement)
        calls = mock_run_vulnerability_scan.call_args_list
        scanned_args = [c[1]["args"][0] for c in calls]
        assert replacement in scanned_args


def test_find_one_and_replace_scans_both_filter_and_replacement(db):
    """find_one_and_replace must scan both filter AND replacement."""
    _filter = {"dog_name": "test", "pswd": "pswd"}
    replacement = {"dog_name": "hacked"}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.find_one_and_replace(_filter, replacement)
        calls = mock_run_vulnerability_scan.call_args_list
        assert len(calls) == 2
        scanned_args = [c[1]["args"][0] for c in calls]
        assert _filter in scanned_args
        assert replacement in scanned_args


# --- no second-arg scan for filter-only operations ---


def test_delete_one_does_not_double_scan(db):
    """delete_one has no update arg — exactly one scan call."""
    _filter = {"dog_name": "test"}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.delete_one(_filter)
        mock_run_vulnerability_scan.assert_called_once()
        assert mock_run_vulnerability_scan.call_args[1]["args"][0] == _filter


def test_delete_many_does_not_double_scan(db):
    """delete_many has no update arg — exactly one scan call."""
    _filter = {"dog_name": "test"}
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.delete_many(_filter)
        mock_run_vulnerability_scan.assert_called_once()
        assert mock_run_vulnerability_scan.call_args[1]["args"][0] == _filter

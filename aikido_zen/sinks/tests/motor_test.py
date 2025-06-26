import asyncio
import pytest
from unittest.mock import patch
import aikido_zen.sinks.pymongo
from aikido_zen.background_process.comms import reset_comms
import pymongo.errors as mongo_errs


@pytest.fixture
def db():
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient("mongodb://admin:password@127.0.0.1:27017")
    return client["my_database"]


@pytest.mark.asyncio
async def test_replace_one(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter, repl = {"dog_name": "test"}, {"dog_name": "dog2", "pswd": "pswd"}
        await dogs.replace_one(filter, repl)

        called_with = mock_run_vulnerability_scan.call_args[1]
        mock_run_vulnerability_scan.assert_any_call(
            args=({"dog_name": "test"},),
            op="pymongo.collection.Collection.replace_one",
            kind="nosql_injection",
        )


@pytest.mark.asyncio
async def test_update_one(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter, update = {"dog_name": "test"}, {"pswd": "pswd"}
        await dogs.update_one(filter, {"$set": update})

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.update_one"
        assert called_with["kind"] == "nosql_injection"


@pytest.mark.asyncio
async def test_update_many(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter, update = {"dog_name": "test"}, {"pswd": "pswd"}
        await dogs.update_many(filter, {"$set": update})

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.update_many"
        assert called_with["kind"] == "nosql_injection"


@pytest.mark.asyncio
async def test_delete_one(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter = {"dog_name": "test"}
        await dogs.delete_one(filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.delete_one"
        assert called_with["kind"] == "nosql_injection"


@pytest.mark.asyncio
async def test_delete_many(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter = {"dog_name": "test"}
        await dogs.delete_many(filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.delete_many"
        assert called_with["kind"] == "nosql_injection"


@pytest.mark.asyncio
async def test_find_one(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        await dogs.find_one(_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_count_documents(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        await dogs.count_documents(_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.count_documents"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_find_one_and_delete(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        await dogs.find_one_and_delete(_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_one_and_delete"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_find_one_and_replace(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        await dogs.find_one_and_replace(
            filter=_filter, replacement={"dog_name": "test2"}
        )

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_one_and_replace"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_find_one_and_update(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        await dogs.find_one_and_update(_filter, {"$set": {"dog_name": "test2"}})

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_one_and_update"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_find_empty(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        dogs.find()
        mock_run_vulnerability_scan.assert_not_called()


@pytest.mark.asyncio
async def test_find_not_empty(db):
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


@pytest.mark.asyncio
async def test_find_raw_batches(db):
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


@pytest.mark.asyncio
async def test_distinct(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        await dogs.distinct("pswd", _filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.distinct"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_distinct_kwargs(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        await dogs.distinct(key="pswd", filter=_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.distinct"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_distinct_empty(db):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        await dogs.distinct("pswd")

        mock_run_vulnerability_scan.assert_not_called()


@pytest.mark.asyncio
async def test_aggregate(db):
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
        async for doc in dogs.aggregate(pipeline):
            pass

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert called_with["op"] == "pymongo.collection.Collection.aggregate"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_aggregate_key(db):
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
        async for doc in dogs.aggregate(pipeline=pipeline):
            pass

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert called_with["op"] == "pymongo.collection.Collection.aggregate"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_aggregate_raw_batches_key(db):
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
        async for doc in dogs.aggregate_raw_batches(pipeline=pipeline):
            pass

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert (
            called_with["op"] == "pymongo.collection.Collection.aggregate_raw_batches"
        )
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_aggregate_raw_batches(db):
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
        async for doc in dogs.aggregate_raw_batches(pipeline):
            pass

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert (
            called_with["op"] == "pymongo.collection.Collection.aggregate_raw_batches"
        )
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_watch(db):
    pipeline = [
        {"$match": {"operationType": "insert"}},  # Only listen for insert operations
        {
            "$project": {
                "fullDocument": 1,  # Include the full document in the output
                "operationType": 1,  # Include the operation type
            }
        },
    ]
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        with pytest.raises(mongo_errs.OperationFailure):
            async with dogs.watch(pipeline) as change_stream:
                async for change in change_stream:
                    pass

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert called_with["op"] == "pymongo.collection.Collection.watch"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_watch_key(db):
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
            async with dogs.watch(pipeline=pipeline) as change_stream:
                pass

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == pipeline
        assert called_with["op"] == "pymongo.collection.Collection.watch"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_write(db):
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
            await dogs.bulk_write(requests)
        except Exception:
            pass
        calls = mock_run_vulnerability_scan.call_args_list

        called_with1 = calls[0][1]
        assert called_with1["args"][0] == {"dog_name": "Buddy1"}
        assert called_with1["op"] == "pymongo.collection.Collection.bulk_write"
        assert called_with1["kind"] == "nosql_injection"

        called_with2 = calls[1][1]
        assert called_with2["args"][0] == {"dog_name": "Max3"}
        assert called_with2["op"] == "pymongo.collection.Collection.bulk_write"
        assert called_with2["kind"] == "nosql_injection"

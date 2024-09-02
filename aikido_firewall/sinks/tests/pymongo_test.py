import pytest
from unittest.mock import patch
import aikido_firewall.sinks.pymongo
from aikido_firewall.background_process.comms import reset_comms
import pymongo.errors as mongo_errs


@pytest.fixture
def db():
    from pymongo import MongoClient

    client = MongoClient("mongodb://admin:password@127.0.0.1:27017")
    return client["my_database"]


def test_replace_one(db):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter, repl = {"dog_name": "test"}, {"dog_name": "dog2", "pswd": "pswd"}
        dogs.replace_one(filter, repl)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.replace_one"
        assert called_with["kind"] == "nosql_injection"


def test_update_one(db):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter, update = {"dog_name": "test"}, {"pswd": "pswd"}
        dogs.update_one(filter, {"$set": update})

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.update_one"
        assert called_with["kind"] == "nosql_injection"


def test_update_many(db):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        filter, update = {"dog_name": "test"}, {"pswd": "pswd"}
        dogs.update_many(filter, {"$set": update})

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == filter
        assert called_with["op"] == "pymongo.collection.Collection.update_many"
        assert called_with["kind"] == "nosql_injection"


def test_delete_one(db):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
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
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
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
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.find_one(_filter)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_one"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_count_documents(db):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
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
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
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
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.find_one_and_replace(_filter, {"dog_name": "test2"})

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_one_and_replace"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()


def test_find_one_and_update(db):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        dogs = db["dogs"]
        _filter = {"dog_name": "test", "pswd": "pswd"}
        dogs.find_one_and_update(_filter, {"$set": {"dog_name": "test2"}})

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == _filter
        assert called_with["op"] == "pymongo.collection.Collection.find_one_and_update"
        assert called_with["kind"] == "nosql_injection"
        mock_run_vulnerability_scan.assert_called_once()

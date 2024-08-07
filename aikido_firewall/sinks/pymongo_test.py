import pytest
from unittest.mock import MagicMock
from aikido_firewall.sinks.pymongo import on_pymongo_import


@pytest.fixture
def mock_pymongo():
    mock_pymongo = MagicMock()
    mock_collection = MagicMock()
    mock_pymongo.Collection = mock_collection
    return mock_pymongo


def test_on_pymongo_import(mocker, mock_pymongo):
    mocker.patch("importhook.copy_module", return_value=mock_pymongo)
    mock_add_wrapped_package = mocker.patch(
        "aikido_firewall.background_process.packages.add_wrapped_package"
    )

    for operation in [
        "replace_one",
        "update_one",
        "update_many",
        "delete_one",
        "delete_many",
        "find_one",
        "count_documents",
        "find_one_and_delete",
        "find_one_and_replace",
        "find_one_and_update",
    ]:
        setattr(
            mock_pymongo.Collection,
            operation,
            MagicMock(return_value="original_result"),
        )

    mocker.patch("aikido_firewall.helpers.logging.logger")
    mocker.patch(
        "aikido_firewall.vulnerabilities.nosql_injection.detect_nosql_injection",
        return_value={"injection": False},
    )
    mocker.patch("aikido_firewall.context.get_current_context", return_value={})
    mocker.patch(
        "aikido_firewall.background_process.get_comms",
        return_value=MagicMock(send_data=MagicMock()),
    )

    modified_pymongo = on_pymongo_import(mock_pymongo)

    for operation in [
        "replace_one",
        "update_one",
        "update_many",
        "delete_one",
        "delete_many",
        "find_one",
        "count_documents",
        "find_one_and_delete",
        "find_one_and_replace",
        "find_one_and_update",
    ]:
        wrapped_function = getattr(modified_pymongo.Collection, operation)
        assert wrapped_function is not None
    # Assert that add_wrapped_package was called with the correct argument
    mock_add_wrapped_package.assert_called_once_with("pymongo")

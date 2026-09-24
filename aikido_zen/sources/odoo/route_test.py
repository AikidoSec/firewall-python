from uuid import UUID

from .route import extract_route_arguments


def test_extract_route_arguments_ignores_objects_that_may_access_the_database():
    class Recordset:
        def __str__(self):
            raise AssertionError("recordset must not be stringified")

    object_id = UUID("12345678-1234-5678-9234-567812345678")
    arguments = {
        "name": "example",
        "page": 3,
        "published": True,
        "object_id": object_id,
        "partner": Recordset(),
        "nested": {"value": "ignored"},
    }

    assert extract_route_arguments(arguments) == {
        "name": "example",
        "page": 3,
        "published": True,
        "object_id": str(object_id),
    }

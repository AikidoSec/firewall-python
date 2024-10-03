import pytest
from aikido_zen.vulnerabilities.nosql_injection import detect_nosql_injection
from aikido_zen.context import Context
from collections import defaultdict, OrderedDict, ChainMap


@pytest.fixture
def create_context():
    def _create_context(
        query=None, headers=None, body=None, cookies=None, route_params=None
    ):
        class RequestContext:
            remote_address = "::1"
            method = "GET"
            url = "http://localhost:4000"
            query = {}
            headers = {}
            body = None
            cookies = {}
            route_params = {}
            source = "express"
            route = "/posts/:id"

        RequestContext.query = query if query else {}
        RequestContext.headers = headers if headers else {}
        RequestContext.body = body
        RequestContext.cookies = cookies if cookies else {}
        RequestContext.route_params = route_params if route_params else {}
        return RequestContext()

    return _create_context


def test_empty_filter_and_request(create_context):
    assert detect_nosql_injection(create_context(), {}) == {}


def test_ignore_if_filter_not_object(create_context):
    assert detect_nosql_injection(create_context(), "abc") == {}


def test_ignore_if_and_not_array(create_context):
    assert detect_nosql_injection(create_context(), {"$and": "abc"}) == {}


def test_ignore_if_or_not_array(create_context):
    assert detect_nosql_injection(create_context(), {"$or": "abc"}) == {}


def test_ignore_if_nor_not_array(create_context):
    assert detect_nosql_injection(create_context(), {"$nor": "abc"}) == {}


def test_ignore_if_nor_empty_array(create_context):
    assert detect_nosql_injection(create_context(), {"$nor": []}) == {}


def test_ignore_if_not_not_object(create_context):
    assert detect_nosql_injection(create_context(), {"$not": "abc"}) == {}


def test_filter_with_string_value_and_empty_request(create_context):
    assert detect_nosql_injection(create_context(), {"title": {"title": "title"}}) == {}


def test_filter_with_ne_and_empty_request(create_context):
    assert detect_nosql_injection(create_context(), {"title": {"$ne": None}}) == {}


def test_filter_with_string_value(create_context):
    assert (
        detect_nosql_injection(
            create_context(body={"title": {"title": "title", "a": "b"}}),
            {"title": {"title": "title", "a": "b"}},
        )
        == {}
    )


def test_using_gt_in_query_parameter(create_context):
    assert detect_nosql_injection(
        create_context(query={"title": {"$gt": ""}}), {"title": {"$gt": ""}}
    ) == {
        "injection": True,
        "source": "query",
        "pathToPayload": ".title",
        "payload": {"$gt": ""},
    }


def test_safe_filter(create_context):
    assert (
        detect_nosql_injection(
            create_context(query={"title": "title"}), {"$and": [{"title": "title"}]}
        )
        == {}
    )


def test_using_ne_in_body(create_context):
    assert detect_nosql_injection(
        create_context(body={"title": {"$ne": None}}), {"title": {"$ne": None}}
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".title",
        "payload": {"$ne": None},
    }


def test_using_ne_in_body_with_chainmap(create_context):
    assert detect_nosql_injection(
        create_context(body={"title": {"$ne": None}}),
        ChainMap({"title": {"$ne": None}}, {}),
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".title",
        "payload": {"$ne": None},
    }


def test_using_ne_in_body_with_ordereddict(create_context):
    assert detect_nosql_injection(
        create_context(body={"title": {"$ne": None}}),
        OrderedDict({"title": {"$ne": None}}),
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".title",
        "payload": {"$ne": None},
    }


def test_using_ne_in_body_different_name(create_context):
    assert detect_nosql_injection(
        create_context(body={"title": {"$ne": None}}), {"myTitle": {"$ne": None}}
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".title",
        "payload": {"$ne": None},
    }


def test_using_ne_in_headers_with_different_name(create_context):
    assert detect_nosql_injection(
        create_context(body={"title": {"$ne": None}}), {"someField": {"$ne": None}}
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".title",
        "payload": {"$ne": None},
    }


def test_using_ne_inside_and(create_context):
    assert detect_nosql_injection(
        create_context(body={"title": {"$ne": None}}),
        {"$and": [{"title": {"$ne": None}}, {"published": True}]},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".title",
        "payload": {"$ne": None},
    }


def test_using_ne_inside_or(create_context):
    assert detect_nosql_injection(
        create_context(body={"title": {"$ne": None}}),
        {"$or": [{"title": {"$ne": None}}, {"published": True}]},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".title",
        "payload": {"$ne": None},
    }


def test_using_ne_inside_nor(create_context):
    assert detect_nosql_injection(
        create_context(body={"title": {"$ne": None}}),
        {"$nor": [{"title": {"$ne": None}}, {"published": True}]},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".title",
        "payload": {"$ne": None},
    }


def test_using_ne_inside_not(create_context):
    assert detect_nosql_injection(
        create_context(body={"title": {"$ne": None}}),
        {"$not": {"title": {"$ne": None}}},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".title",
        "payload": {"$ne": None},
    }


def test_using_ne_nested_in_body(create_context):
    assert detect_nosql_injection(
        create_context(body={"nested": {"nested": {"$ne": None}}}),
        {"$not": {"title": {"$ne": None}}},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".nested.nested",
        "payload": {"$ne": None},
    }


def test_using_ne_in_jwt_in_headers(create_context):
    assert detect_nosql_injection(
        create_context(
            # JWT token with the following payload:
            # {
            #   "sub": "1234567890",
            #   "username": {
            #     "$ne": null
            #   },
            #   "iat": 1516239022
            # }
            headers={
                "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ"
            }
        ),
        {"username": {"$ne": None}},
    ) == {
        "injection": True,
        "source": "headers",
        "pathToPayload": ".Authorization<jwt>.username",
        "payload": {"$ne": None},
    }


def test_using_ne_in_jwt_in_bearer_header(create_context):
    assert detect_nosql_injection(
        create_context(
            # JWT token with the following payload:
            # {
            #   "sub": "1234567890",
            #   "username": {
            #     "$ne": null
            #   },
            #   "iat": 1516239022
            # }
            headers={
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ"
            }
        ),
        {"username": {"$ne": None}},
    ) == {
        "injection": True,
        "source": "headers",
        "pathToPayload": ".Authorization<jwt>.username",
        "payload": {"$ne": None},
    }


def test_using_ne_in_jwt_in_cookies(create_context):
    assert detect_nosql_injection(
        create_context(
            # JWT token with the following payload:
            # {
            #   "sub": "1234567890",
            #   "username": {
            #     "$ne": null
            #   },
            #   "iat": 1516239022
            # }
            cookies={
                "session": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ"
            }
        ),
        {"username": {"$ne": None}},
    ) == {
        "injection": True,
        "source": "cookies",
        "pathToPayload": ".session<jwt>.username",
        "payload": {"$ne": None},
    }


def test_jwt_lookalike(create_context):
    assert (
        detect_nosql_injection(
            create_context(
                cookies={
                    "session": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbW!iOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ"
                }
            ),
            {"username": {"$ne": None}},
        )
        == {}
    )


def test_using_gt_in_query_parameter(create_context):
    assert detect_nosql_injection(
        create_context(query={"age": {"$gt": "21"}}), {"age": {"$gt": "21"}}
    ) == {
        "injection": True,
        "source": "query",
        "pathToPayload": ".age",
        "payload": {"$gt": "21"},
    }


def test_using_gt_in_query_parameter_with_other_params(create_context):
    assert detect_nosql_injection(
        create_context(query={"age": {"$gt": "21"}}),
        {"age": {"$gt": "21", "test": "true"}},
    ) == {
        "injection": True,
        "source": "query",
        "pathToPayload": ".age",
        "payload": {"$gt": "21"},
    }


def test_using_filter_as_body(create_context):
    assert detect_nosql_injection(
        create_context(body={"$gt": "21", "pswd": "Test"}),
        {"$gt": "21", "pswd": "Test"},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".",
        "payload": {"$gt": "21"},
    }


def test_using_gt_and_lt_in_query_parameter(create_context):
    assert detect_nosql_injection(
        create_context(body={"age": {"$gt": "21", "$lt": "100"}}),
        {"age": {"$gt": "21", "$lt": "100"}},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".age",
        "payload": {"$gt": "21", "$lt": "100"},
    }


def test_using_gt_and_lt_in_query_parameter_different_name(create_context):
    assert detect_nosql_injection(
        create_context(body={"age": {"$gt": "21", "$lt": "100"}}),
        {"myAge": {"$gt": "21", "$lt": "100"}},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".age",
        "payload": {"$gt": "21", "$lt": "100"},
    }


def test_using_gt_and_lt_in_query_parameter_nested(create_context):
    assert detect_nosql_injection(
        create_context(
            body={"nested": {"nested": {"age": {"$gt": "21", "$lt": "100"}}}}
        ),
        {"$and": [{"someAgeField": {"$gt": "21", "$lt": "100"}}]},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".nested.nested.age",
        "payload": {"$gt": "21", "$lt": "100"},
    }


def test_using_gt_and_lt_in_query_parameter_root(create_context):
    assert detect_nosql_injection(
        create_context(body={"$and": [{"someAgeField": {"$gt": "21", "$lt": "100"}}]}),
        {"$and": [{"someAgeField": {"$gt": "21", "$lt": "100"}}]},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".",
        "payload": {"$and": [{"someAgeField": {"$gt": "21", "$lt": "100"}}]},
    }


def test_where(create_context):
    assert detect_nosql_injection(
        create_context(body={"$and": [{"$where": "sleep(1000)"}]}),
        {"$and": [{"$where": "sleep(1000)"}]},
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".",
        "payload": {"$and": [{"$where": "sleep(1000)"}]},
    }


def test_array_body(create_context):
    assert detect_nosql_injection(
        create_context(
            body=[
                {
                    "$where": "sleep(1000)",
                },
            ]
        ),
        {
            "$and": [
                {
                    "$where": "sleep(1000)",
                },
            ],
        },
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".[0]",
        "payload": {"$where": "sleep(1000)"},
    }


def test_safe_email_password(create_context):
    assert (
        detect_nosql_injection(
            create_context(
                body={
                    "email": "email",
                    "password": "password",
                }
            ),
            {
                "email": "email",
                "password": "password",
            },
        )
        == {}
    )


def test_flags_pipeline_aggregations(create_context):
    assert detect_nosql_injection(
        create_context(
            body=[
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "Dummy-IdontExist",
                        "foreignField": "Dummy-IdontExist",
                        "as": "user_docs",
                    },
                },
                {
                    "$limit": 1,
                },
            ]
        ),
        [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "Dummy-IdontExist",
                    "foreignField": "Dummy-IdontExist",
                    "as": "user_docs",
                },
            },
            {
                "$limit": 1,
            },
        ],
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".[0]",
        "payload": {
            "$lookup": {
                "from": "users",
                "localField": "Dummy-IdontExist",
                "foreignField": "Dummy-IdontExist",
                "as": "user_docs",
            },
        },
    }

    assert detect_nosql_injection(
        create_context(
            body={
                "username": {
                    "$gt": "",
                },
            }
        ),
        [
            {
                "$match": {
                    "username": {
                        "$gt": "",
                    },
                },
            },
            {
                "$group": {
                    "_id": "$username",
                    "count": {"$sum": 1},
                },
            },
        ],
    ) == {
        "injection": True,
        "source": "body",
        "pathToPayload": ".username",
        "payload": {
            "$gt": "",
        },
    }


def test_ignores_safe_pipeline_aggregations(create_context):
    assert (
        detect_nosql_injection(
            create_context(
                body={
                    "username": "admin",
                }
            ),
            [
                {
                    "$match": {
                        "username": "admin",
                    },
                },
                {
                    "$group": {
                        "_id": "$username",
                        "count": {"$sum": 1},
                    },
                },
            ],
        )
        == {}
    )

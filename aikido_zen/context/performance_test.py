import time
from urllib.parse import parse_qs
from aikido_zen.context import Context


def test_set_framework_query_costs_less_than_parsing_the_query():
    query_string = "&".join(f"a=%ff{i}" for i in range(5000))
    context = Context(
        req={
            "REQUEST_METHOD": "GET",
            "wsgi.url_scheme": "http",
            "HTTP_HOST": "localhost:8080",
            "PATH_INFO": "/hello",
            "QUERY_STRING": query_string,
            "REMOTE_ADDR": "198.51.100.23",
        },
        source="flask",
    )
    raw_query = context.query
    merge_time = parse_time = float("inf")
    for _ in range(5):
        context.query = raw_query
        framework_query = {"a": [f"%FF{i}" for i in range(5000)]}
        start = time.perf_counter()
        context.set_framework_query(framework_query)
        merge_time = min(merge_time, time.perf_counter() - start)
        start = time.perf_counter()
        parse_qs(query_string)
        parse_time = min(parse_time, time.perf_counter() - start)
    assert len(context.query["a"]) == 10000
    assert merge_time < parse_time

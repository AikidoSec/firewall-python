import pytest
from unittest.mock import AsyncMock, MagicMock

from . import starlette_routing


@pytest.mark.asyncio
async def test_pre_response_runs_when_the_body_cannot_be_read(monkeypatch):
    request_handler = MagicMock(return_value=None)
    monkeypatch.setattr(starlette_routing, "request_handler", request_handler)
    monkeypatch.setattr(
        starlette_routing,
        "extract_data_from_request",
        AsyncMock(side_effect=ValueError("Expected boundary character")),
    )
    route = AsyncMock(return_value="response")

    response = await starlette_routing.aik_route_func_wrapper(route)(MagicMock())

    request_handler.assert_any_call(stage="pre_response")
    route.assert_awaited_once()
    assert response == "response"

import pytest
from unittest.mock import AsyncMock, MagicMock

import aikido_zen.test_utils as test_utils
from aikido_zen.context import current_context
from .quart import _handle_request_before


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    current_context.set(None)


async def original(request):
    return None


@pytest.mark.asyncio
async def test_unparsable_json_body_falls_back_to_the_raw_body():
    context = test_utils.generate_and_set_context()
    request = MagicMock(is_json=True)
    request.form = AsyncMock(return_value={})()
    request.get_json = AsyncMock(side_effect=RecursionError("Stack overflow"))
    request.get_data = AsyncMock(return_value=b"[[[1' OR 1=1 -- ")
    request.cookies.to_dict.return_value = {"session": "abc"}

    await _handle_request_before(original, None, (request,), {})

    assert context.body == "[[[1' OR 1=1 -- "
    assert context.cookies == {"session": "abc"}

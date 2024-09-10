"""Exports function extract_data_from_request"""

from aikido_zen.context import get_current_context


async def extract_data_from_request(request):
    """Extracts json, form_data or body from Starlette request"""
    context = get_current_context()
    if not context:
        return

    # Parse data
    try:
        context.body = await request.json()
    except ValueError:
        # Throws error if the body is not json
        pass
    if not context.body:
        context.body = await request.form()
    if not context.body:
        context.body = await request.body()

    context.set_as_current_context()

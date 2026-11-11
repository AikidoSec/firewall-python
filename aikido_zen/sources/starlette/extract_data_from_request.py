"""Exports function extract_data_from_request"""

from aikido_zen.context import get_current_context


async def extract_data_from_request(request):
    """Extracts json, form_data or body from Starlette request"""
    context = get_current_context()
    if not context:
        return

    # Parse data
    try:
        context.set_body(await request.json())
    except (ValueError, RecursionError):
        # Not JSON, or nested too deep to parse
        pass
    if not context.body or _is_form_urlencoded(request):
        try:
            form_data = await request.form()
        except Exception:
            form_data = None
        if form_data:
            # Convert to dict object :
            form = dict(form_data.items())
            context.set_body([context.body, form] if context.body else form)
    if not context.body:
        context.set_body(await request.body())

    context.set_as_current_context()


def _is_form_urlencoded(request):
    # Lowercased and without parameters, like Starlette when it picks the form parser.
    content_type = request.headers.get("content-type", "").split(";")[0]
    return content_type.strip().lower() == "application/x-www-form-urlencoded"

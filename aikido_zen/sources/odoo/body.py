_FORM_MIMETYPES = {
    "application/x-www-form-urlencoded",
    "multipart/form-data",
}
_JSON_ROUTE_TYPES = {"json", "jsonrpc", "json2"}


def extract_body(request, routing_type):
    httprequest = request.httprequest

    if routing_type in _JSON_ROUTE_TYPES:
        if routing_type == "json2" and not httprequest.content_length:
            return None
        return request.get_json_data()

    mimetype = (getattr(httprequest, "mimetype", "") or "").lower()
    if mimetype == "application/json" or mimetype.endswith("+json"):
        return request.get_json_data()

    if mimetype in _FORM_MIMETYPES:
        form = httprequest.form
        if hasattr(form, "lists"):
            return {key: list(values) for key, values in form.lists()}
        return dict(form)

    return httprequest.get_data(cache=True)

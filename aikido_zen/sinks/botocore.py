from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import after, on_import, patch_function, before


@after
def _debug_after(func, instance, args, kwargs, return_value):
    # Extract arguments to validate later
    operation_name = get_argument(args, kwargs, 0, "operation_name")
    api_params = get_argument(args, kwargs, 1, "api_params")
    if not operation_name or not api_params or not return_value:
        return

    # Validate arguments, we only want to check operations related to AI.
    if operation_name.lower() != "converse":
        return
    register_call("botocore.client.Converse", "ai_op")

    model_id = str(api_params.get("modelId", ""))
    if not model_id:
        return None

    usage = return_value.get("usage", {})
    on_ai_call(
        provider="bedrock",
        model=model_id,
        input_tokens=usage.get("inputTokens", 0),
        output_tokens=usage.get("outputTokens", 0),
    )


@on_import("botocore.client")
def patch(m):
    patch_function(m, "BaseClient._make_api_call", _debug_after)

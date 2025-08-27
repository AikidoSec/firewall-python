from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import after, on_import, patch_function, before


def get_tokens_from_converse(api_response):
    usage = api_response.get("usage", {})
    input_tokens = usage.get("inputTokens", 0)
    output_tokens = usage.get("outputTokens", 0)
    return int(input_tokens), int(output_tokens)


def get_tokens_from_invoke_model(api_response):
    headers = api_response.get("ResponseMetadata", {}).get("HTTPHeaders", {})
    input_tokens_str = headers.get("x-amzn-bedrock-input-token-count", "0")
    output_tokens_str = headers.get("x-amzn-bedrock-output-token-count", "0")
    return int(input_tokens_str), int(output_tokens_str)


@after
def make_api_call_after(func, instance, args, kwargs, return_value):
    # Extract arguments to validate later
    operation_name = get_argument(args, kwargs, 0, "operation_name")
    api_params = get_argument(args, kwargs, 1, "api_params")
    if not operation_name or not api_params or not return_value:
        return

    # Validate arguments, we only want to check operations related to AI.
    if operation_name not in ["Converse", "InvokeModel"]:
        return
    register_call(f"botocore.client.{operation_name}", "ai_op")

    model_id = str(api_params.get("modelId", ""))
    if not model_id:
        return None

    input_tokens, output_tokens = (0, 0)
    if operation_name == "Converse":
        input_tokens, output_tokens = get_tokens_from_converse(return_value)
    elif operation_name == "InvokeModel":
        input_tokens, output_tokens = get_tokens_from_invoke_model(return_value)

    on_ai_call("bedrock", model_id, input_tokens, output_tokens)


@on_import("botocore.client")
def patch(m):
    patch_function(m, "BaseClient._make_api_call", make_api_call_after)

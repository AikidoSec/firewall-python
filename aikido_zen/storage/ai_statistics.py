import copy

# Tool names come from the response, so cap them at the server's heartbeat limits.
MAX_TOOL_NAME_LENGTH = 255
MAX_TOOLS = 1000


class AIStatistics:
    def __init__(self):
        self.calls = {}
        self.tools = {}

    def ensure_provider_stats(self, provider, model):
        key = get_provider_key(provider, model)

        if key not in self.calls:
            self.calls[key] = {
                "provider": provider,
                "model": model,
                "calls": 0,
                "tokens": {
                    "input": 0,
                    "output": 0,
                    "total": 0,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                },
            }

        return self.calls[key]

    def on_ai_call(
        self, provider, model, input_tokens, output_tokens, cache_read=0, cache_write=0
    ):
        if not provider or not model:
            return

        provider_stats = self.ensure_provider_stats(provider, model)
        provider_stats["calls"] += 1
        provider_stats["tokens"]["input"] += input_tokens
        provider_stats["tokens"]["output"] += output_tokens
        provider_stats["tokens"]["total"] += input_tokens + output_tokens
        provider_stats["tokens"]["cacheRead"] += cache_read
        provider_stats["tokens"]["cacheWrite"] += cache_write

    def on_ai_tool_call(self, provider, model, name, calls=1):
        if not provider or not model or not isinstance(name, str) or not name:
            return
        if len(name) > MAX_TOOL_NAME_LENGTH:
            return

        key = (provider, model, name)
        tool = self.tools.get(key)
        if tool is None:
            if len(self.tools) >= MAX_TOOLS:
                return
            row = {"provider": provider, "model": model, "name": name, "calls": 0}
            # Another thread may have added the same row since the get() above.
            tool = self.tools.setdefault(key, row)
        tool["calls"] += calls

    def get_stats(self):
        # Copy the rows first, because another thread may add one during the loop.
        return [copy.deepcopy(stats) for stats in list(self.calls.values())]

    def get_tool_stats(self):
        return [dict(tool) for tool in list(self.tools.values())]

    def import_list(self, ai_stats_list):
        for new_entry in ai_stats_list:
            existing_entry = self.ensure_provider_stats(
                new_entry["provider"], new_entry["model"]
            )
            existing_entry["calls"] += new_entry["calls"]
            for field in existing_entry["tokens"]:
                existing_entry["tokens"][field] += new_entry["tokens"].get(field, 0)

    def import_tool_list(self, tool_list):
        for tool in tool_list:
            self.on_ai_tool_call(
                tool["provider"], tool["model"], tool["name"], tool["calls"]
            )

    def clear(self):
        self.calls.clear()
        self.tools.clear()

    def empty(self):
        return len(self.calls) == 0 and len(self.tools) == 0


def get_provider_key(provider, model):
    return f"{provider}:{model}"

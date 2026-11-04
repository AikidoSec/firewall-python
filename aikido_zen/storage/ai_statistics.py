import copy


class AIStatistics:
    def __init__(self):
        self.calls = {}

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
        add_cache_tokens(provider_stats["tokens"], cache_read, cache_write)

    def get_stats(self):
        return [copy.deepcopy(stats) for stats in self.calls.values()]

    def import_list(self, ai_stats_list):
        for new_entry in ai_stats_list:
            existing_entry = self.ensure_provider_stats(
                new_entry["provider"], new_entry["model"]
            )
            existing_entry["calls"] += new_entry["calls"]
            existing_entry["tokens"]["input"] += new_entry["tokens"]["input"]
            existing_entry["tokens"]["output"] += new_entry["tokens"]["output"]
            existing_entry["tokens"]["total"] += new_entry["tokens"]["total"]
            add_cache_tokens(
                existing_entry["tokens"],
                new_entry["tokens"].get("cacheRead", 0),
                new_entry["tokens"].get("cacheWrite", 0),
            )

    def clear(self):
        self.calls.clear()

    def empty(self):
        return len(self.calls) == 0


def get_provider_key(provider, model):
    return f"{provider}:{model}"


def add_cache_tokens(tokens, cache_read, cache_write):
    # Not every caller reports cached tokens (the SDK sinks do not), so the keys are
    # only added once some were reported.
    if cache_read:
        tokens["cacheRead"] = tokens.get("cacheRead", 0) + cache_read
    if cache_write:
        tokens["cacheWrite"] = tokens.get("cacheWrite", 0) + cache_write

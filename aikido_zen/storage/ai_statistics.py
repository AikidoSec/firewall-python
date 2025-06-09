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

    def on_ai_call(self, provider, model, input_tokens, output_tokens):
        if not provider or not model:
            return

        provider_stats = self.ensure_provider_stats(provider, model)
        provider_stats["calls"] += 1
        provider_stats["tokens"]["input"] += input_tokens
        provider_stats["tokens"]["output"] += output_tokens
        provider_stats["tokens"]["total"] += input_tokens + output_tokens

    def get_stats(self):
        return [copy.deepcopy(stats) for stats in self.calls.values()]

    def clear(self):
        self.calls.clear()

    def is_empty(self):
        return len(self.calls) == 0


def get_provider_key(provider, model):
    return f"{provider}:{model}"

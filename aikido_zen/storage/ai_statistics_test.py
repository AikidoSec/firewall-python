import sys
import threading

import pytest
from .ai_statistics import AIStatistics


@pytest.fixture
def stats():
    return AIStatistics()


def test_initializes_with_empty_state(stats):
    assert stats.get_stats() == []
    assert stats.empty() is True


def test_tracks_basic_ai_calls(stats):
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )

    result = stats.get_stats()
    assert len(result) == 1
    assert result[0] == {
        "provider": "openai",
        "model": "gpt-4",
        "calls": 1,
        "tokens": {
            "input": 100,
            "output": 50,
            "total": 150,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }

    assert stats.empty() is False


def test_tracks_multiple_calls_to_same_provider_model(stats):
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )

    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=200, output_tokens=75
    )

    result = stats.get_stats()
    assert len(result) == 1
    assert result[0] == {
        "provider": "openai",
        "model": "gpt-4",
        "calls": 2,
        "tokens": {
            "input": 300,
            "output": 125,
            "total": 425,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }


def test_tracks_different_provider_model_combinations_separately(stats):
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )

    stats.on_ai_call(
        provider="openai", model="gpt-3.5-turbo", input_tokens=80, output_tokens=40
    )

    stats.on_ai_call(
        provider="anthropic", model="claude-3", input_tokens=120, output_tokens=60
    )

    result = stats.get_stats()
    assert len(result) == 3

    # Sort by provider:model for consistent testing
    result.sort(key=lambda x: f"{x['provider']}:{x['model']}")

    assert result[0] == {
        "provider": "anthropic",
        "model": "claude-3",
        "calls": 1,
        "tokens": {
            "input": 120,
            "output": 60,
            "total": 180,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }

    assert result[1] == {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "calls": 1,
        "tokens": {
            "input": 80,
            "output": 40,
            "total": 120,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }

    assert result[2] == {
        "provider": "openai",
        "model": "gpt-4",
        "calls": 1,
        "tokens": {
            "input": 100,
            "output": 50,
            "total": 150,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }


def test_resets_all_statistics(stats):
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )

    stats.on_ai_call(
        provider="anthropic", model="claude-3", input_tokens=120, output_tokens=60
    )

    assert stats.empty() is False
    assert len(stats.get_stats()) == 2

    stats.clear()

    assert stats.empty() is True
    assert stats.get_stats() == []


def test_handles_zero_token_inputs(stats):
    stats.on_ai_call(provider="openai", model="gpt-4", input_tokens=0, output_tokens=0)

    result = stats.get_stats()
    assert len(result) == 1
    assert result[0]["tokens"] == {
        "input": 0,
        "output": 0,
        "total": 0,
        "cacheRead": 0,
        "cacheWrite": 0,
    }


def test_called_with_empty_provider(stats):
    stats.on_ai_call(provider="", model="gpt-4", input_tokens=100, output_tokens=50)

    assert stats.empty() is True


def test_called_with_empty_model(stats):
    stats.on_ai_call(provider="openai", model="", input_tokens=100, output_tokens=50)

    assert stats.empty() is True


def test_get_stats_returns_immutable_data(stats):
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )

    result = stats.get_stats()
    result[0]["calls"] = 100
    result[0]["tokens"]["input"] = 1000

    # Verify that the internal state has not changed
    assert stats.get_stats()[0]["calls"] == 1


def test_get_stats_returns_new_list(stats):
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )

    result1 = stats.get_stats()
    result2 = stats.get_stats()

    # Modify the first result to ensure it doesn't affect the second result
    result1[0]["calls"] = 200

    # Verify that the second result is unchanged
    assert result2 == [
        {
            "provider": "openai",
            "model": "gpt-4",
            "calls": 1,
            "tokens": {
                "input": 100,
                "output": 50,
                "total": 150,
                "cacheRead": 0,
                "cacheWrite": 0,
            },
        }
    ]


def test_get_stats_returns_deep_copy(stats):
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )

    result = stats.get_stats()

    # Modify the result deeply to ensure it doesn't affect the internal state
    result[0]["tokens"]["input"] = 200

    # Verify that the internal state has not changed
    assert stats.get_stats()[0]["tokens"]["input"] == 100


def test_get_stats_consistency_after_multiple_calls(stats):
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )

    stats.on_ai_call(
        provider="anthropic", model="claude-3", input_tokens=120, output_tokens=60
    )

    result1 = stats.get_stats()
    result2 = stats.get_stats()

    # Modify the first result to ensure it doesn't affect the second result
    result1[0]["calls"] = 300

    # Verify that the second result is unchanged
    assert result2 == [
        {
            "provider": "openai",
            "model": "gpt-4",
            "calls": 1,
            "tokens": {
                "input": 100,
                "output": 50,
                "total": 150,
                "cacheRead": 0,
                "cacheWrite": 0,
            },
        },
        {
            "provider": "anthropic",
            "model": "claude-3",
            "calls": 1,
            "tokens": {
                "input": 120,
                "output": 60,
                "total": 180,
                "cacheRead": 0,
                "cacheWrite": 0,
            },
        },
    ]


def test_import_list_with_empty_stats(stats):
    # Test importing a list into empty statistics
    stats.import_list(
        [
            {
                "provider": "openai",
                "model": "gpt-4",
                "calls": 1,
                "tokens": {
                    "input": 100,
                    "output": 50,
                    "total": 150,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                },
            },
            {
                "provider": "anthropic",
                "model": "claude-3",
                "calls": 1,
                "tokens": {
                    "input": 120,
                    "output": 60,
                    "total": 180,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                },
            },
        ]
    )

    result = stats.get_stats()
    assert len(result) == 2
    assert result[0] == {
        "provider": "openai",
        "model": "gpt-4",
        "calls": 1,
        "tokens": {
            "input": 100,
            "output": 50,
            "total": 150,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }
    assert result[1] == {
        "provider": "anthropic",
        "model": "claude-3",
        "calls": 1,
        "tokens": {
            "input": 120,
            "output": 60,
            "total": 180,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }


def test_import_list_with_existing_stats(stats):
    # Add some initial statistics
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )

    # Import a list that includes an existing provider:model combination
    stats.import_list(
        [
            {
                "provider": "openai",
                "model": "gpt-4",
                "calls": 1,
                "tokens": {
                    "input": 200,
                    "output": 100,
                    "total": 300,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                },
            },
            {
                "provider": "anthropic",
                "model": "claude-3",
                "calls": 1,
                "tokens": {
                    "input": 120,
                    "output": 60,
                    "total": 180,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                },
            },
        ]
    )

    result = stats.get_stats()
    assert len(result) == 2
    assert result[0] == {
        "provider": "openai",
        "model": "gpt-4",
        "calls": 2,  # Initial call + imported call
        "tokens": {
            "input": 300,  # 100 + 200
            "output": 150,  # 50 + 100
            "total": 450,  # 150 + 300
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }
    assert result[1] == {
        "provider": "anthropic",
        "model": "claude-3",
        "calls": 1,
        "tokens": {
            "input": 120,
            "output": 60,
            "total": 180,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }


def test_import_list_with_overlapping_and_new_entries(stats):
    # Add some initial statistics
    stats.on_ai_call(
        provider="openai", model="gpt-4", input_tokens=100, output_tokens=50
    )
    stats.on_ai_call(
        provider="anthropic", model="claude-3", input_tokens=120, output_tokens=60
    )

    # Import a list that includes both existing and new provider:model combinations
    stats.import_list(
        [
            {
                "provider": "openai",
                "model": "gpt-4",
                "calls": 1,
                "tokens": {
                    "input": 200,
                    "output": 100,
                    "total": 300,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                },
            },
            {
                "provider": "anthropic",
                "model": "claude-3",
                "calls": 1,
                "tokens": {
                    "input": 120,
                    "output": 60,
                    "total": 180,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                },
            },
            {
                "provider": "mistral",
                "model": "mistral-7b",
                "calls": 1,
                "tokens": {
                    "input": 150,
                    "output": 75,
                    "total": 225,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                },
            },
        ]
    )

    result = stats.get_stats()
    assert len(result) == 3
    result.sort(key=lambda x: f"{x['provider']}:{x['model']}")

    assert result[0] == {
        "provider": "anthropic",
        "model": "claude-3",
        "calls": 2,  # Initial call + imported call
        "tokens": {
            "input": 240,  # 120 + 120
            "output": 120,  # 60 + 60
            "total": 360,  # 180 + 180
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }
    assert result[1] == {
        "provider": "mistral",
        "model": "mistral-7b",
        "calls": 1,
        "tokens": {
            "input": 150,
            "output": 75,
            "total": 225,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }
    assert result[2] == {
        "provider": "openai",
        "model": "gpt-4",
        "calls": 2,  # Initial call + imported call
        "tokens": {
            "input": 300,  # 100 + 200
            "output": 150,  # 50 + 100
            "total": 450,  # 150 + 300
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }


def test_tracks_cache_tokens(stats):
    stats.on_ai_call(
        provider="anthropic", model="claude-3", input_tokens=100, output_tokens=10
    )
    assert stats.get_stats()[0]["tokens"] == {
        "input": 100,
        "output": 10,
        "total": 110,
        "cacheRead": 0,
        "cacheWrite": 0,
    }

    stats.on_ai_call(
        provider="anthropic",
        model="claude-3",
        input_tokens=100,
        output_tokens=10,
        cache_read=40,
        cache_write=5,
    )
    stats.on_ai_call(
        provider="anthropic",
        model="claude-3",
        input_tokens=50,
        output_tokens=10,
        cache_read=20,
    )
    assert stats.get_stats()[0]["tokens"] == {
        "input": 250,
        "output": 30,
        "total": 280,
        "cacheRead": 60,
        "cacheWrite": 5,
    }


def test_import_list_adds_cache_tokens(stats):
    stats.on_ai_call(
        provider="openai",
        model="gpt-4",
        input_tokens=100,
        output_tokens=50,
        cache_read=40,
    )
    stats.import_list(
        [
            {
                "provider": "openai",
                "model": "gpt-4",
                "calls": 2,
                "tokens": {"input": 30, "output": 20, "total": 50, "cacheWrite": 7},
            },
            {
                "provider": "openai",
                "model": "gpt-4",
                "calls": 1,
                "tokens": {"input": 10, "output": 5, "total": 15, "cacheRead": 4},
            },
        ]
    )
    assert stats.get_stats() == [
        {
            "provider": "openai",
            "model": "gpt-4",
            "calls": 4,
            "tokens": {
                "input": 140,
                "output": 75,
                "total": 215,
                "cacheRead": 44,
                "cacheWrite": 7,
            },
        }
    ]


def test_tracks_tool_calls_per_provider_model_and_name(stats):
    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "search")
    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "search")
    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o-mini", "search")
    stats.on_ai_tool_call("http://localhost:4000", "gpt-4o", "search")
    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "fetch")

    assert stats.get_tool_stats() == [
        {
            "provider": "https://api.openai.com",
            "model": "gpt-4o",
            "name": "search",
            "calls": 2,
        },
        {
            "provider": "https://api.openai.com",
            "model": "gpt-4o-mini",
            "name": "search",
            "calls": 1,
        },
        {
            "provider": "http://localhost:4000",
            "model": "gpt-4o",
            "name": "search",
            "calls": 1,
        },
        {
            "provider": "https://api.openai.com",
            "model": "gpt-4o",
            "name": "fetch",
            "calls": 1,
        },
    ]
    assert stats.empty() is False


@pytest.mark.parametrize(
    "provider, model, name",
    [
        ("", "gpt-4o", "search"),
        ("https://api.openai.com", "", "search"),
        ("https://api.openai.com", "gpt-4o", ""),
        ("https://api.openai.com", "gpt-4o", None),
        ("https://api.openai.com", "gpt-4o", 5),
        ("https://api.openai.com", "gpt-4o", "x" * 256),
    ],
)
def test_ignores_invalid_tool_calls(stats, provider, model, name):
    stats.on_ai_tool_call(provider, model, name)

    assert stats.get_tool_stats() == []
    assert stats.empty() is True


def test_keeps_a_tool_name_of_the_maximum_length(stats):
    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "x" * 255)

    assert [tool["name"] for tool in stats.get_tool_stats()] == ["x" * 255]


def test_keeps_at_most_1000_tools(stats):
    for i in range(1001):
        stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", f"tool-{i}")
    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "tool-0")

    tools = stats.get_tool_stats()
    assert len(tools) == 1000
    assert tools[0]["calls"] == 2
    assert "tool-1000" not in [tool["name"] for tool in tools]


def test_import_tool_list_adds_to_existing_tools(stats):
    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "search")

    stats.import_tool_list(
        [
            {
                "provider": "https://api.openai.com",
                "model": "gpt-4o",
                "name": "search",
                "calls": 3,
            },
            {
                "provider": "https://api.openai.com",
                "model": "gpt-4o",
                "name": "fetch",
                "calls": 1,
            },
        ]
    )

    assert stats.get_tool_stats() == [
        {
            "provider": "https://api.openai.com",
            "model": "gpt-4o",
            "name": "search",
            "calls": 4,
        },
        {
            "provider": "https://api.openai.com",
            "model": "gpt-4o",
            "name": "fetch",
            "calls": 1,
        },
    ]


def test_clear_resets_tool_calls(stats):
    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "search")

    stats.clear()

    assert stats.get_tool_stats() == []
    assert stats.empty() is True


def test_get_tool_stats_returns_copies(stats):
    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "search")

    stats.get_tool_stats()[0]["calls"] = 99

    assert stats.get_tool_stats()[0]["calls"] == 1


class ToolAddedByAnotherThread(dict):
    def get(self, key, default=None):
        row = super().get(key, default)
        if row is None:
            provider, model, name = key
            self[key] = {"provider": provider, "model": model, "name": name, "calls": 1}
        return row


def test_keeps_a_tool_that_another_thread_adds_at_the_same_time(stats):
    stats.tools = ToolAddedByAnotherThread()

    stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "search")

    assert stats.get_tool_stats()[0]["calls"] == 2


@pytest.mark.parametrize("read", ["get_stats", "get_tool_stats"])
def test_reading_while_other_threads_add_rows_does_not_fail(stats, read):
    switch_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    barrier = threading.Barrier(9)
    errors = []

    def add_rows(thread):
        barrier.wait(5)
        for i in range(200):
            stats.on_ai_call("https://api.openai.com", f"m-{thread}-{i}", 1, 1)
            stats.on_ai_tool_call("https://api.openai.com", "m", f"t-{thread}-{i}")

    writers = [threading.Thread(target=add_rows, args=(t,)) for t in range(8)]
    try:
        for writer in writers:
            writer.start()
        barrier.wait(5)
        while any(writer.is_alive() for writer in writers):
            try:
                getattr(stats, read)()
            except RuntimeError as error:
                errors.append(error)
    finally:
        sys.setswitchinterval(switch_interval)
        for writer in writers:
            writer.join(5)
            assert not writer.is_alive()
    assert errors == []

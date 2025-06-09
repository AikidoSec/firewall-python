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
            },
        },
    ]

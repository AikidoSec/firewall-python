import pytest

from .ai_provider_hosts import ALL_HOSTS, get_ai_provider


@pytest.mark.parametrize(
    "host, provider",
    [
        ("api.openai.com", "openai"),
        ("API.OpenAI.com", "openai"),
        ("my-resource.openai.azure.com", "azure"),
        ("my-resource.cognitiveservices.azure.com", "azure"),
        ("api.mistral.ai", "mistral"),
        ("api.groq.com", "groq"),
        ("api.anthropic.com", "anthropic"),
        ("generativelanguage.googleapis.com", "gemini"),
        ("us-central1-aiplatform.googleapis.com", "vertex_ai"),
        ("openrouter.ai", "openrouter"),
        ("api.eu.mistral.ai", "mistral"),
        ("codestral.mistral.ai", "codestral"),
        ("api.cohere.com", "cohere"),
        ("my-project.services.ai.azure.com", "azure_ai"),
        ("api.business.githubcopilot.com", "github_copilot"),
        ("api.fastino.ai", "pioneer"),
    ],
)
def test_known_hosts(host, provider):
    assert get_ai_provider(host, "openai_compatible") == provider


@pytest.mark.parametrize(
    "host",
    [
        "api.openai.com.evil.com",
        "a.b.openai.azure.com",
        "openai.azure.com",
        ".openai.azure.com",
        "a.b.services.ai.azure.com",
        "litellm.internal",
        "localhost",
    ],
)
def test_other_hosts_get_the_default(host):
    assert get_ai_provider(host, "openai_compatible") == "openai_compatible"


def test_host_list_has_no_duplicates():
    hosts = [host for host, _ in ALL_HOSTS]
    assert len(hosts) == len(set(hosts))

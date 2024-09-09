import pytest
import random
from aikido_zen.helpers.looks_like_a_secret import looks_like_a_secret

LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NUMBERS = "0123456789"
SPECIALS = "!#$%^&*|;:<>"
MINIMUM_LENGTH = 10


def secret_from_charset(length, charset):
    return "".join(random.choice(charset) for _ in range(length))


def test_empty_string():
    assert looks_like_a_secret("") == False


def test_short_strings():
    short_strings = [
        "c",
        "NR",
        "7t3",
        "4qEK",
        "KJr6s",
        "KXiW4a",
        "Fupm2Vi",
        "jiGmyGfg",
        "SJPLzVQ8t",
        "OmNf04j6mU",
    ]
    for s in short_strings:
        assert looks_like_a_secret(s) == False


def test_long_strings():
    assert looks_like_a_secret("rsVEExrR2sVDONyeWwND") == True
    assert looks_like_a_secret(":2fbg;:qf$BRBc<2AG8&") == True


def test_very_long_strings():
    assert (
        looks_like_a_secret(
            "efDJHhzvkytpXoMkFUgag6shWJktYZ5QUrUCTfecFELpdvaoAT3tekI4ZhpzbqLt"
        )
        == True
    )
    assert (
        looks_like_a_secret(
            "XqSwF6ySwMdTomIdmgFWcMVXWf5L0oVvO5sIjaCPI7EjiPvRZhZGWx3A6mLl1HXPOHdUeabsjhngW06JiLhAchFwgtUaAYXLolZn75WsJVKHxEM1mEXhlmZepLCGwRAM"
        )
        == True
    )


def test_contains_white_space():
    assert looks_like_a_secret("rsVEExrR2sVDONyeWwND ") == False


def test_less_than_2_charsets():
    assert looks_like_a_secret(secret_from_charset(10, LOWERCASE)) == False
    assert looks_like_a_secret(secret_from_charset(10, UPPERCASE)) == False
    assert looks_like_a_secret(secret_from_charset(10, NUMBERS)) == False
    assert looks_like_a_secret(secret_from_charset(10, SPECIALS)) == False


def test_common_url_terms():
    url_terms = [
        "development",
        "programming",
        "applications",
        "implementation",
        "environment",
        "technologies",
        "documentation",
        "demonstration",
        "configuration",
        "administrator",
        "visualization",
        "international",
        "collaboration",
        "opportunities",
        "functionality",
        "customization",
        "specifications",
        "optimization",
        "contributions",
        "accessibility",
        "subscription",
        "subscriptions",
        "infrastructure",
        "architecture",
        "authentication",
        "sustainability",
        "notifications",
        "announcements",
        "recommendations",
        "communication",
        "compatibility",
        "enhancement",
        "integration",
        "performance",
        "improvements",
        "introduction",
        "capabilities",
        "communities",
        "credentials",
        "integration",
        "permissions",
        "validation",
        "serialization",
        "deserialization",
        "rate-limiting",
        "throttling",
        "load-balancer",
        "microservices",
        "endpoints",
        "data-transfer",
        "encryption",
        "authorization",
        "bearer-token",
        "multipart",
        "urlencoded",
        "api-docs",
        "postman",
        "json-schema",
        "serialization",
        "deserialization",
        "rate-limiting",
        "throttling",
        "load-balancer",
        "api-gateway",
        "microservices",
        "endpoints",
        "data-transfer",
        "encryption",
        "signature",
        "poppins-bold-webfont.woff2",
        "karla-bold-webfont.woff2",
        "startEmailBasedLogin",
        "jenkinsFile",
        "ConnectionStrings.config",
        "coach",
        "login",
        "payment_methods",
        "activity_logs",
        "feedback_responses",
        "balance_transactions",
        "customer_sessions",
        "payment_intents",
        "billing_portal",
        "subscription_items",
        "namedLayouts",
        "PlatformAction",
        "quickActions",
        "queryLocator",
        "relevantItems",
        "parameterizedSearch",
    ]
    for term in url_terms:
        assert looks_like_a_secret(term) == False


def test_known_word_separators():
    assert looks_like_a_secret("this-is-a-secret-1") == False


def test_number_is_not_a_secret():
    assert looks_like_a_secret("1234567890") == False
    assert looks_like_a_secret("1234567890" * 2) == False


def test_known_secrets():
    secrets = [
        "yqHYTS<agpi^aa1",
        "hIofuWBifkJI5iVsSNKKKDpBfmMqJJwuXMxau6AS8WZaHVLDAMeJXo3BwsFyrIIm",
        "AG7DrGi3pDDIUU1PrEsj",
        "CnJ4DunhYfv2db6T1FRfciRBHtlNKOYrjoz",
        "Gic*EfMq:^MQ|ZcmX:yW1",
        "AG7DrGi3pDDIUU1PrEsj",
    ]
    for secret in secrets:
        assert looks_like_a_secret(secret) == True

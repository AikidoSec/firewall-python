from .firewall_lists import FirewallLists


def test_monitored_ip_matches_multiple_lists():
    firewall_lists = FirewallLists()
    firewall_lists.set_monitored_ips(
        [
            {"key": "list1", "source": "s", "description": "d", "ips": ["1.2.3.0/24"]},
            {"key": "list2", "source": "s", "description": "d", "ips": ["1.2.3.4"]},
        ]
    )
    assert firewall_lists.get_matching_monitored_ip_list_keys("1.2.3.4") == [
        "list1",
        "list2",
    ]
    assert firewall_lists.get_matching_monitored_ip_list_keys("9.9.9.9") == []


def test_monitored_user_agent():
    firewall_lists = FirewallLists()
    assert not firewall_lists.is_monitored_user_agent("ClaudeBot")
    assert not firewall_lists.is_monitored_user_agent("")
    assert not firewall_lists.is_monitored_user_agent(None)

    firewall_lists.set_monitored_user_agents("ClaudeBot|GPTBot")
    assert firewall_lists.is_monitored_user_agent("claudebot/1.0")
    assert not firewall_lists.is_monitored_user_agent("curl/8.0")

    firewall_lists.set_monitored_user_agents("")
    assert not firewall_lists.is_monitored_user_agent("ClaudeBot/1.0")


def test_user_agent_details_skip_invalid_pattern():
    firewall_lists = FirewallLists()
    firewall_lists.set_user_agent_details(
        [
            {"key": "broken", "pattern": "["},
            {"key": "claudebot", "pattern": "ClaudeBot"},
            {"key": "gptbot", "pattern": "GPTBot"},
        ]
    )
    assert firewall_lists.get_matching_user_agent_keys("ClaudeBot/1.0") == ["claudebot"]
    assert firewall_lists.get_matching_user_agent_keys("curl/8.0") == []


def test_invalid_monitored_user_agent_pattern_is_skipped():
    firewall_lists = FirewallLists()
    firewall_lists.set_monitored_user_agents("ClaudeBot")
    firewall_lists.set_monitored_user_agents("[abc")
    assert not firewall_lists.is_monitored_user_agent("ClaudeBot/1.0")

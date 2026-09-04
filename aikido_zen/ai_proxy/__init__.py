"""
Wires the AI proxy's two halves together: the in-process `AiCoreServer` (rules
down, events up) and the `ProxySupervisor` (spawns the Rust binary).

`maybe_start` is meant to be called once, from inside `AikidoBackgroundProcess`,
which already gives exactly-once-per-host semantics for free.
"""

from aikido_zen.helpers.env_vars.feature_flags import is_feature_enabled
from aikido_zen.helpers.logging import logger

from .core_server import AiCoreServer
from .supervisor import ProxySupervisor


class AiProxyManager:
    def __init__(self, token, get_connection_manager, event_sink):
        self.get_connection_manager = get_connection_manager
        self.core_server = AiCoreServer(
            config_provider=self._config_provider, event_sink=event_sink
        )
        self.supervisor = ProxySupervisor(token=token, core_url=self.core_server.url)

    def _config_provider(self):
        connection_manager = self.get_connection_manager()
        if connection_manager is None:
            return {"ai_enabled": True, "blocked_ai_tools": [], "ai_rules": []}
        return {
            "ai_enabled": True,
            "blocked_ai_tools": connection_manager.conf.blocked_ai_tools,
            "ai_rules": connection_manager.conf.ai_rules,
        }

    def start(self):
        """Returns True if the proxy was spawned. False (with core_server torn
        back down) if no binary could be found."""
        self.core_server.start()
        if not self.supervisor.start():
            self.core_server.stop()
            return False
        return True

    def stop(self):
        self.supervisor.stop()
        self.core_server.stop()


def maybe_start(token, get_connection_manager, event_sink):
    """Starts the AI proxy if the feature is enabled, returning the manager
    (for shutdown) or None."""
    if not is_feature_enabled("ai_proxy"):
        return None
    if not token:
        return None

    manager = AiProxyManager(
        token=token, get_connection_manager=get_connection_manager, event_sink=event_sink
    )
    try:
        if not manager.start():
            return None
    except Exception as e:
        logger.debug("Failed to start AI proxy: %s", e)
        return None
    return manager

"""
Resolves the path to the zen-ai-proxy (safechain-l7-proxy, built with the
`ai-only` cargo feature) binary.

Packaging (bundling a per-platform binary in the wheel, or downloading one at
runtime like `aikido_zen/libs/libzen_internals_*`) is future work. For now this
only supports an explicit override, which is what local development and tests
use.
"""

import os
import platform

from aikido_zen.helpers.logging import logger

ENV_OVERRIDE = "AIKIDO_AI_PROXY_BIN"


def resolve_binary_path():
    """Returns a path to the AI proxy binary, or None if it can't be found."""
    override = os.getenv(ENV_OVERRIDE)
    if override:
        if os.path.isfile(override):
            return override
        logger.debug(
            "%s is set to %s, but no file exists there", ENV_OVERRIDE, override
        )
        return None

    bundled = _bundled_path()
    if bundled and os.path.isfile(bundled):
        return bundled

    return None


def _bundled_path():
    """Where a future packaging step would place a per-platform binary,
    mirroring aikido_zen/vulnerabilities/sql_injection/get_lib_path.py."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    name = "zen-ai-proxy.exe" if system == "windows" else "zen-ai-proxy"
    libs_dir = os.path.join(os.path.dirname(__file__), "..", "libs")
    return os.path.join(libs_dir, f"{name}-{system}-{machine}")

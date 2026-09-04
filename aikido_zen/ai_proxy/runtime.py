"""
Discovery file the background process publishes once the AI proxy is up,
and worker processes read to find it.

A deterministic path (not data delivered over SYNC_DATA) because SDK clients
are often constructed at import time, before a worker has synced with the
background process even once.
"""

import json
import os
import time

from aikido_zen.helpers.get_temp_dir import get_temp_dir
from aikido_zen.helpers.hash_aikido_token import hash_aikido_token
from aikido_zen.helpers.logging import logger


def get_runtime_file():
    """Path to the AI proxy's discovery file, one per host+token."""
    return os.path.join(
        get_temp_dir(), f"aikido_ai_proxy_{hash_aikido_token()}.json"
    )


def write_runtime_info(proxy_port, ca_path, pid):
    """Atomically publishes the AI proxy's connection info for workers to read."""
    path = get_runtime_file()
    tmp_path = f"{path}.{os.getpid()}.tmp"
    payload = {
        "proxy_port": proxy_port,
        "ca_path": ca_path,
        "pid": pid,
        "written_at": time.time(),
    }
    try:
        with open(tmp_path, "w") as f:
            json.dump(payload, f)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, path)
    except OSError as e:
        logger.debug("Failed to write AI proxy runtime file: %s", e)
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def clear_runtime_info():
    try:
        os.remove(get_runtime_file())
    except OSError:
        pass


def read_runtime_info():
    """Returns {"proxy_port", "ca_path", "pid", "written_at"} or None."""
    try:
        with open(get_runtime_file(), "r") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None

    if not isinstance(data, dict):
        return None
    if not isinstance(data.get("proxy_port"), int):
        return None
    if not isinstance(data.get("ca_path"), str) or not os.path.exists(data["ca_path"]):
        return None
    return data

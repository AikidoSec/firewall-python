"""
Spawns and supervises the zen-ai-proxy child process.

The proxy holds no cloud credentials: `--aikido-url`/`--reporting-endpoint`
both point at the in-process `AiCoreServer`, never at Aikido's cloud.
"""

import json
import os
import subprocess
import threading
import time
import urllib.error
import urllib.request

from aikido_zen.helpers.get_temp_dir import get_temp_dir
from aikido_zen.helpers.hash_aikido_token import hash_aikido_token
from aikido_zen.helpers.logging import logger

from .binary import resolve_binary_path
from .core_server import free_port
from .runtime import clear_runtime_info, write_runtime_info

READY_TIMEOUT_SECONDS = 30
RESTART_BACKOFF_SECONDS = [1, 2, 5, 10, 30]


class ProxySupervisor:
    def __init__(self, token, core_url, upstream_proxy_url=None):
        self.token = token
        self.core_url = core_url
        # Test-only: chains the proxy's egress through another local proxy
        # (e.g. a canned upstream standing in for a real provider) instead of
        # the real internet. Never set in production.
        self.upstream_proxy_url = upstream_proxy_url
        self.data_dir = os.path.join(
            get_temp_dir(), f"aikido_ai_proxy_{hash_aikido_token()}"
        )
        self._proc = None
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        """Starts the supervisor thread. No-op (logged) if the binary can't be found."""
        binary_path = resolve_binary_path()
        if not binary_path:
            logger.debug(
                "No AI proxy binary found (set AIKIDO_AI_PROXY_BIN); "
                "AI tool-call visibility disabled."
            )
            return False

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "secrets"), exist_ok=True)
        self._ensure_exec_bit(binary_path)
        self._write_agent_identity()

        self._thread = threading.Thread(
            target=self._run, args=(binary_path,), name="zen-ai-proxy-supervisor",
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self):
        self._stop_event.set()
        self._kill_child()
        clear_runtime_info()

    @staticmethod
    def _ensure_exec_bit(path):
        try:
            mode = os.stat(path).st_mode
            os.chmod(path, mode | 0o111)
        except OSError:
            pass

    def _write_agent_identity(self):
        # The proxy refuses to talk to any cloud-backed subsystem without this
        # file, even though we never point it at a real cloud.
        config_path = os.path.join(self.data_dir, "config.json")
        try:
            with open(config_path, "w") as f:
                json.dump({"token": str(self.token), "device_id": "zen-python-agent"}, f)
        except OSError as e:
            logger.debug("Failed to write AI proxy config.json: %s", e)

    def _build_argv(self, binary_path, proxy_port, meta_port):
        argv = [
            binary_path,
            "--bind", f"127.0.0.1:{proxy_port}",
            "--meta", f"127.0.0.1:{meta_port}",
            "--secrets", os.path.join(self.data_dir, "secrets"),
            "-D", self.data_dir,
            "--aikido-url", self.core_url,
            "--reporting-endpoint", self.core_url,
        ]
        if self.upstream_proxy_url:
            argv += ["--proxy", self.upstream_proxy_url]
        return argv

    def _run(self, binary_path):
        backoff_index = 0
        while not self._stop_event.is_set():
            proxy_port = free_port()
            meta_port = free_port()
            argv = self._build_argv(binary_path, proxy_port, meta_port)
            log_path = os.path.join(self.data_dir, "proxy.log")
            started_at = time.monotonic()
            try:
                with open(log_path, "a") as log_file:
                    self._proc = subprocess.Popen(
                        argv, stdout=log_file, stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
            except OSError as e:
                logger.debug("Failed to spawn AI proxy: %s", e)
                return

            if self._wait_ready(meta_port):
                self._fetch_ca_and_publish(meta_port, proxy_port)
                backoff_index = 0
            else:
                logger.debug("AI proxy did not become ready; see %s", log_path)

            self._proc.wait()
            clear_runtime_info()
            if self._stop_event.is_set():
                return

            # A proxy that dies within seconds of starting is not going to
            # recover; back off instead of spinning.
            if time.monotonic() - started_at < 5:
                delay = RESTART_BACKOFF_SECONDS[
                    min(backoff_index, len(RESTART_BACKOFF_SECONDS) - 1)
                ]
                backoff_index += 1
            else:
                delay = RESTART_BACKOFF_SECONDS[0]
                backoff_index = 0
            self._stop_event.wait(delay)

    def _wait_ready(self, meta_port):
        deadline = time.monotonic() + READY_TIMEOUT_SECONDS
        while time.monotonic() < deadline and not self._stop_event.is_set():
            if self._proc.poll() is not None:
                return False
            try:
                urllib.request.urlopen(
                    f"http://127.0.0.1:{meta_port}/ping", timeout=1
                ).read()
                return True
            except (urllib.error.URLError, OSError):
                time.sleep(0.2)
        return False

    def _fetch_ca_and_publish(self, meta_port, proxy_port):
        try:
            pem = urllib.request.urlopen(
                f"http://127.0.0.1:{meta_port}/ca", timeout=5
            ).read()
        except (urllib.error.URLError, OSError) as e:
            logger.debug("Failed to fetch AI proxy CA: %s", e)
            return

        ca_path = os.path.join(self.data_dir, "ca.pem")
        try:
            with open(ca_path, "wb") as f:
                f.write(pem)
            os.chmod(ca_path, 0o600)
        except OSError as e:
            logger.debug("Failed to write AI proxy CA to disk: %s", e)
            return

        write_runtime_info(proxy_port=proxy_port, ca_path=ca_path, pid=self._proc.pid)

    def _kill_child(self):
        proc = self._proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            except OSError:
                pass

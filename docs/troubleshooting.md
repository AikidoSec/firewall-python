# Troubleshooting

## Review installation steps

Double-check your setup against the [installation guide](../README.md#installation).
Make sure:
- The package installed correctly.
- The firewall is initialized early in your app (before routes or handlers).
- Your framework-specific integration (middleware, decorator, etc.) matches the example in the README.
- You’re running a supported runtime version for your language.

## Check connection to Aikido

The firewall must be able to reach Aikido’s API endpoints.

Test from the same environment where your app runs and follow the instructions on this page: https://help.aikido.dev/zen-firewall/miscellaneous/outbound-network-connections-for-zen

## Check logs for errors

Common places:
- Docker: `docker logs <your-app-container>`
- systemd: `journalctl -u <your-app-service> --since "1 hour ago"`
- Local dev: your terminal or IDE run console

Tip: search for lines that contain `aikido_zen`.

## Enable debug logs temporarily

Set the `AIKIDO_DEBUG=true` environment variable before starting your app to surface initialization and connection details.

This will make Zen log additional information during startup and operation.

## Contact support

If you still can’t resolve the issue:

- Use the in-app chat to reach our support team directly.
- Or create an issue on [GitHub](https://github.com/AikidoSec/firewall-python/issues) with details about your setup, framework, and logs.

Include as much context as possible (framework, logs, and how Aikido was added) so we can help you quickly.

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
from dotenv import load_dotenv
import os
load_dotenv()
firewall_disabled = os.getenv("FIREWALL_DISABLED")
if firewall_disabled is not None:
    if firewall_disabled.lower() != "1":
        import aikido_firewall # Aikido package import
        aikido_firewall.protect()

import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample-django-postgres-app.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

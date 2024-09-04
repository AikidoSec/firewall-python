"""
Aggregates from the different modules
"""

# pylint: disable=import-outside-toplevel

from dotenv import load_dotenv

# Re-export set_current_user :
from aikido_firewall.context.users import set_user

# Import logger
from aikido_firewall.helpers.logging import logger

# Import background process
from aikido_firewall.background_process import start_background_process

# Load environment variables and constants
# Load environment variables and constants
from aikido_firewall.config import PKG_VERSION

load_dotenv()


def protect(mode="daemon"):
    """
    Mode can be set to :
    - daemon : Default, imports sinks/sources and starts background_process
    - daemon_only: Only starts background process and doesn't wrap
    - daemon_disabled : This will import sinks/sources but won't start a background process
    Protect user's application
    """
    if mode in ("daemon", "daemon_only"):
        start_background_process()
    if mode == "daemon_only":
        # Do not import sinks/sources
        return
    if mode == "daemon_disabled":
        logger.debug("Not starting the background process, daemon disabled.")

    # Import sources
    import aikido_firewall.sources.django
    import aikido_firewall.sources.flask
    import aikido_firewall.sources.quart
    import aikido_firewall.sources.xml
    import aikido_firewall.sources.lxml

    import aikido_firewall.sources.gunicorn
    import aikido_firewall.sources.uwsgi

    # Import DB Sinks
    import aikido_firewall.sinks.pymysql
    import aikido_firewall.sinks.mysqlclient
    import aikido_firewall.sinks.pymongo
    import aikido_firewall.sinks.psycopg2
    import aikido_firewall.sinks.psycopg
    import aikido_firewall.sinks.asyncpg
    import aikido_firewall.sinks.builtins
    import aikido_firewall.sinks.os
    import aikido_firewall.sinks.http_client
    import aikido_firewall.sinks.socket

    # Import shell sinks
    import aikido_firewall.sinks.os_system
    import aikido_firewall.sinks.subprocess

    logger.info("Aikido python firewall v%s starting.", PKG_VERSION)

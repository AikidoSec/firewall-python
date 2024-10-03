"""
Aggregates from the different modules
"""

# pylint: disable=import-outside-toplevel

from dotenv import load_dotenv

# Re-export set_current_user :
from aikido_zen.context.users import set_user

# Import logger
from aikido_zen.helpers.logging import logger

# Import background process
from aikido_zen.background_process import start_background_process

# Load environment variables and constants
from aikido_zen.config import PKG_VERSION
from aikido_zen.helpers.aikido_disabled_flag_active import aikido_disabled_flag_active

load_dotenv()


def protect(mode="daemon"):
    """
    Mode can be set to :
    - daemon : Default, imports sinks/sources and starts background_process
    - daemon_only: Only starts background process and doesn't wrap
    - daemon_disabled : This will import sinks/sources but won't start a background process
    Protect user's application
    """
    if aikido_disabled_flag_active():
        # Do not run any aikido code when the disabled flag is on
        return
    if mode in ("daemon", "daemon_only"):
        start_background_process()
    if mode == "daemon_only":
        # Do not import sinks/sources
        return
    if mode == "daemon_disabled":
        logger.debug("Not starting the background process, daemon disabled.")

    # Import sources
    import aikido_zen.sources.django
    import aikido_zen.sources.flask
    import aikido_zen.sources.quart
    import aikido_zen.sources.starlette
    import aikido_zen.sources.xml
    import aikido_zen.sources.lxml

    import aikido_zen.sources.gunicorn
    import aikido_zen.sources.uwsgi

    # Import DB Sinks
    import aikido_zen.sinks.pymysql
    import aikido_zen.sinks.mysqlclient
    import aikido_zen.sinks.pymongo
    import aikido_zen.sinks.psycopg2
    import aikido_zen.sinks.psycopg
    import aikido_zen.sinks.asyncpg
    import aikido_zen.sinks.builtins
    import aikido_zen.sinks.os
    import aikido_zen.sinks.shutil
    import aikido_zen.sinks.io
    import aikido_zen.sinks.http_client
    import aikido_zen.sinks.socket

    # Import shell sinks
    import aikido_zen.sinks.os_system
    import aikido_zen.sinks.subprocess

    logger.info("Zen by Aikido v%s starting.", PKG_VERSION)

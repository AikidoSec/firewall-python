"""
Aggregates from the different modules
"""

import os

from aikido_zen.background_process.test_uds_file_access import test_uds_file_access

# Re-export functions :
from aikido_zen.lambda_helper import protect_lambda
from aikido_zen.context.users import set_user
from aikido_zen.middleware import should_block_request

# Import logger
from aikido_zen.helpers.logging import logger

# Import background process
from aikido_zen.background_process import start_background_process

# Load environment variables and constants
from aikido_zen.config import PKG_VERSION
from aikido_zen.helpers.aikido_disabled_flag_active import aikido_disabled_flag_active


def protect(mode="daemon", token=""):
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
    if not test_uds_file_access():
        return  # Unable to start background process

    if token:
        os.environ["AIKIDO_TOKEN"] = token

    if mode in ("daemon", "daemon_only"):
        start_background_process()
    if mode == "daemon_only":
        # Do not import sinks/sources
        return
    if mode == "daemon_disabled":
        logger.debug("Not starting the background process, daemon disabled.")

    import aikido_zen.sinks.builtins_import

    # Import sources
    import aikido_zen.sources.django
    import aikido_zen.sources.flask
    import aikido_zen.sources.quart
    import aikido_zen.sources.starlette
    import aikido_zen.sources.xml_sources.xml
    import aikido_zen.sources.xml_sources.lxml

    # Import DB Sinks
    import aikido_zen.sinks.pymysql
    import aikido_zen.sinks.mysqlclient
    import aikido_zen.sinks.pymongo
    import aikido_zen.sinks.psycopg2
    import aikido_zen.sinks.psycopg
    import aikido_zen.sinks.asyncpg
    import aikido_zen.sinks.clickhouse_driver

    import aikido_zen.sinks.builtins
    import aikido_zen.sinks.os
    import aikido_zen.sinks.shutil
    import aikido_zen.sinks.io
    import aikido_zen.sinks.http_client
    import aikido_zen.sinks.socket

    # Import shell sinks
    import aikido_zen.sinks.os_system
    import aikido_zen.sinks.subprocess

    # Import AI sinks
    import aikido_zen.sinks.openai
    import aikido_zen.sinks.anthropic
    import aikido_zen.sinks.mistralai
    import aikido_zen.sinks.botocore

    logger.info("Zen by Aikido v%s starting.", PKG_VERSION)

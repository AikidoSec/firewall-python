"""
Aggregates from the different modules
"""

# Re-export set_current_user :
from aikido_firewall.context.users import set_user

from dotenv import load_dotenv

# Import logger
from aikido_firewall.helpers.logging import logger

# Import background process
from aikido_firewall.background_process import start_background_process

# Load environment variables
load_dotenv()


def protect(module="any", server=True):
    """
    Protect user's application
    """
    if server:
        start_background_process()
    else:
        logger.debug("Not starting background process")
    if module == "background-process-only":
        return

    # Import sources
    import aikido_firewall.sources.django

    if not module in ["django", "django-gunicorn"]:
        import aikido_firewall.sources.flask

    import aikido_firewall.sources.gunicorn
    import aikido_firewall.sources.uwsgi

    # Import DB Sinks
    import aikido_firewall.sinks.pymysql
    import aikido_firewall.sinks.mysqlclient
    import aikido_firewall.sinks.pymongo
    import aikido_firewall.sinks.psycopg2
    import aikido_firewall.sinks.builtins
    import aikido_firewall.sinks.os
    import aikido_firewall.sinks.http_client
    import aikido_firewall.sinks.socket

    # Import shell sinks
    import aikido_firewall.sinks.os_system
    import aikido_firewall.sinks.subprocess

    logger.info("Aikido python firewall started")

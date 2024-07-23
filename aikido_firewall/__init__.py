"""
Aggregates from the different modules
"""

from dotenv import load_dotenv


# Import logger
from aikido_firewall.helpers.logging import logger

# Import agent
from aikido_firewall.agent import start_ipc

# Load environment variables
load_dotenv()


def protect(module="any", server=True):
    """Start Aikido agent"""
    if server:
        start_ipc()
    else:
        logger.debug("Not starting IPC server")
    if module == "server-only":
        return

    # Import sources
    if module == "django":
        import aikido_firewall.sources.django

    if not module in ["django", "django-gunicorn"]:
        import aikido_firewall.sources.flask

    # Import sinks
    import aikido_firewall.sinks.pymysql

    logger.info("Aikido python firewall started")

"""
Aggregates from the different modules
"""

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
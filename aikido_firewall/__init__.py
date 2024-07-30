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


def protect(module="any"):
    """
    Protect user's application
    """
    # Import sources
    import aikido_firewall.sources.django

    if module != "django":
        import aikido_firewall.sources.flask

    # Import sinks
    import aikido_firewall.sinks.pymysql
    import aikido_firewall.sinks.pymongo

    logger.info("Aikido python firewall started")
    start_background_process()

"""
Aggregates from the different modules
"""

from dotenv import load_dotenv


# Import logger
from aikido_firewall.helpers.logging import logger

# Import agent
from aikido_firewall.agent import start_agent

# Load environment variables
load_dotenv()


def protect(module="any"):
    """Start Aikido agent"""
    # Import sources
    import aikido_firewall.sources.django

    if module != "django":
        import aikido_firewall.sources.flask

    # Import sinks
    import aikido_firewall.sinks.pymysql

    logger.info("Aikido python firewall started")
    start_agent()

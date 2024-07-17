"""
Aggregates from the different modules
"""

from dotenv import load_dotenv

# Import sources
import aikido_firewall.sources.django
import aikido_firewall.sources.flask

# Import sinks
import aikido_firewall.sinks.pymysql

# Import middleware
import aikido_firewall.middleware.django

# Import logger
from aikido_firewall.helpers.logging import logger

# Import agent
from aikido_firewall.agent import start_agent

# Load environment variables
load_dotenv()


def protect():
    """Start Aikido agent"""
    logger.info("Aikido python firewall started")
    start_agent()

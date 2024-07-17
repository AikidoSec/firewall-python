"""
Aggregates from the different modules
"""

from dotenv import load_dotenv

# Import sources
import aikido_firewall.sources.django
from aikido_firewall.sources.flask import start as flask_start

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
    agent = start_agent()
    flask_start(agent)

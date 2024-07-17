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

# Load environment variables
load_dotenv()

logger.info("Aikido python firewall started")

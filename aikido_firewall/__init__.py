"""
Aggregates from the different modules
"""

# Import sources
import aikido_firewall.sources.django
import aikido_firewall.sources.flask

# Import middleware
import aikido_firewall.middleware.django

# Import logger
from aikido_firewall.helpers.logging import logger

logger.info("Aikido python firewall started")

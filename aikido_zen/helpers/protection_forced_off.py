"""Exports protection_forced_off"""

from .match_endpoints import match_endpoints


def protection_forced_off(route_metadata, endpoints):
    """Matches the route from given endpoints and returns boolean whether protection is off."""
    matches = match_endpoints(route_metadata, endpoints)
    if matches and len(matches) > 0:
        for match in matches:
            if match.get("forceProtectionOff"):
                return True
    return False

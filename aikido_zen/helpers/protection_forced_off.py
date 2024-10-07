"""Exports protection_forced_off"""

from .match_endpoints import match_endpoints


def protection_forced_off(route_metadata, endpoints):
    """Matches the route from given endpoints and returns boolean wether protection is off."""
    matches = match_endpoints(route_metadata, endpoints)
    if matches and len(matches) > 0:
        return matches[0]["forceProtectionOff"]
    return False

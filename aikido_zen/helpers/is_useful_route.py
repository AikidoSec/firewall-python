"""
Main export is the is_useful_route function
"""

import os

EXCLUDED_METHODS = ["OPTIONS", "HEAD"]
IGNORE_EXTENSIONS = ["properties", "config", "webmanifest"]
IGNORE_STRINGS = ["cgi-bin"]


def is_useful_route(status_code, route, method):
    """
    Checks if the route is actually useful,
    - Isn't OPTIONS or HEAD
    - Status code isn't an error or redirect code
    - Isn't a dot file e.g. .well-known
    - etc.
    """
    status_code = int(status_code)

    is_valid_code = status_code >= 200 and status_code < 400
    if not is_valid_code:
        # Status code needs to be between 200 and 400 in order for it to be "useful"
        return False

    if method in EXCLUDED_METHODS:
        return False

    segments = route.split("/")

    # Do not discover routes with dot files like `/path/to/.file` or `/.directory/file`
    # We want to allow discovery of well-known URIs like `/.well-known/acme-challenge`
    if not is_well_known_uri(route) and any(
        is_dot_file(segment) for segment in segments
    ):
        return False

    if any(contains_ignored_string(segment) for segment in segments):
        return False

    return all(is_allowed_extension(segment) for segment in segments)


def is_allowed_extension(segment):
    """Checks if the extension on the file is allowed"""
    extension = os.path.splitext(segment)[1]

    if extension and extension.startswith("."):
        extension = extension[1:]  # Remove the dot from the extension

        if 2 <= len(extension) <= 5:
            return False

        if extension in IGNORE_EXTENSIONS:
            return False

    return True


def is_dot_file(segment):
    """Checks if the current segment is a dot file"""
    return segment.startswith(".") and len(segment) > 1


def contains_ignored_string(segment):
    """Checks if the current segment contains ignored strings"""
    return any(ignored_str in segment for ignored_str in IGNORE_STRINGS)


well_known = {
    "/.well-known/acme-challenge",
    "/.well-known/amphtml",
    "/.well-known/api-catalog",
    "/.well-known/appspecific",
    "/.well-known/ashrae",
    "/.well-known/assetlinks.json",
    "/.well-known/broadband-labels",
    "/.well-known/brski",
    "/.well-known/caldav",
    "/.well-known/carddav",
    "/.well-known/change-password",
    "/.well-known/cmp",
    "/.well-known/coap",
    "/.well-known/coap-eap",
    "/.well-known/core",
    "/.well-known/csaf",
    "/.well-known/csaf-aggregator",
    "/.well-known/csvm",
    "/.well-known/did.json",
    "/.well-known/did-configuration.json",
    "/.well-known/dnt",
    "/.well-known/dnt-policy.txt",
    "/.well-known/dots",
    "/.well-known/ecips",
    "/.well-known/edhoc",
    "/.well-known/enterprise-network-security",
    "/.well-known/enterprise-transport-security",
    "/.well-known/est",
    "/.well-known/genid",
    "/.well-known/gnap-as-rs",
    "/.well-known/gpc.json",
    "/.well-known/gs1resolver",
    "/.well-known/hoba",
    "/.well-known/host-meta",
    "/.well-known/host-meta.json",
    "/.well-known/hosting-provider",
    "/.well-known/http-opportunistic",
    "/.well-known/idp-proxy",
    "/.well-known/jmap",
    "/.well-known/keybase.txt",
    "/.well-known/knx",
    "/.well-known/looking-glass",
    "/.well-known/masque",
    "/.well-known/matrix",
    "/.well-known/mercure",
    "/.well-known/mta-sts.txt",
    "/.well-known/mud",
    "/.well-known/nfv-oauth-server-configuration",
    "/.well-known/ni",
    "/.well-known/nodeinfo",
    "/.well-known/nostr.json",
    "/.well-known/oauth-authorization-server",
    "/.well-known/oauth-protected-resource",
    "/.well-known/ohttp-gateway",
    "/.well-known/openid-federation",
    "/.well-known/open-resource-discovery",
    "/.well-known/openid-configuration",
    "/.well-known/openorg",
    "/.well-known/oslc",
    "/.well-known/pki-validation",
    "/.well-known/posh",
    "/.well-known/privacy-sandbox-attestations.json",
    "/.well-known/private-token-issuer-directory",
    "/.well-known/probing.txt",
    "/.well-known/pvd",
    "/.well-known/rd",
    "/.well-known/related-website-set.json",
    "/.well-known/reload-config",
    "/.well-known/repute-template",
    "/.well-known/resourcesync",
    "/.well-known/sbom",
    "/.well-known/security.txt",
    "/.well-known/ssf-configuration",
    "/.well-known/sshfp",
    "/.well-known/stun-key",
    "/.well-known/terraform.json",
    "/.well-known/thread",
    "/.well-known/time",
    "/.well-known/timezone",
    "/.well-known/tdmrep.json",
    "/.well-known/tor-relay",
    "/.well-known/tpcd",
    "/.well-known/traffic-advice",
    "/.well-known/trust.txt",
    "/.well-known/uma2-configuration",
    "/.well-known/void",
    "/.well-known/webfinger",
    "/.well-known/webweaver.json",
    "/.well-known/wot",
}


def is_well_known_uri(path):
    """Check if a path is a well-known URI"""
    """e.g. /.well-known/acme-challenge"""
    """https://www.iana.org/assignments/well-known-uris/well-known-uris.xhtml"""
    return path in well_known

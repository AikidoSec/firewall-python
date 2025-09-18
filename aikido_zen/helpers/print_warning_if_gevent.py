from .logging import logger


def print_warning_if_gevent(pkg_name: str, pkg_version: str):
    if pkg_name == "gevent":
        logger.warning(
            "\ngevent is not compatible with Aikido Zen. \n"
            + "due to the way gevent monkey-patches and alters the behaviour of "
            + "python-native modules (like `multiprocessing`), \nZen cannot function with gevent installed. "
            + "Find out more in the gunicorn docs for Zen."
        )

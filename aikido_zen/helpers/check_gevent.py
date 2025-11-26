import sys


def check_gevent():
    if "gevent" in sys.modules:
        print(
            "\033[1m"  # bold
            + "\nWARNING: gevent is not compatible with Aikido Zen.\n"
            + "\033[0m"  # reset
            + "Due to the way gevent monkey-patches and alters the behaviour of "
            + "Python-native modules (like \033[1m`multiprocessing`\033[0m), \n"
            + "\033[1mZen cannot function with gevent installed.\033[0m "
            + "Find out more in the gUnicorn docs for Zen."
        )
        return True
    return False

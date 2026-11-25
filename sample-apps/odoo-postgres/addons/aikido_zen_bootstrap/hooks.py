import aikido_zen


def post_load():
    aikido_zen.protect()

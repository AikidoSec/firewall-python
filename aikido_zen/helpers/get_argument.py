"""Exports get_argument"""


def get_argument(args, kwargs, pos, name):
    """Checks kwargs and args for your argument"""
    if name in kwargs:
        return kwargs.get(name)
    if args and len(args) > pos:
        return args[pos]
    return None

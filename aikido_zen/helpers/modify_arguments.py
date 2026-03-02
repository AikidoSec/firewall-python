"""Exports modify_arguments"""


def modify_arguments(args, kwargs, pos, name, value):
    """
    Returns (new_args, new_kwargs) with `value` injected as keyword argument
    `name`. If a positional argument exists at index `pos` or beyond, it is
    removed from args so the call is not duplicated.
    """
    if len(args) > pos:
        new_args = args[:pos] + (value,) + args[pos + 1 :]
        new_kwargs = dict(kwargs)
    else:
        new_args = args
        new_kwargs = dict(kwargs)
        new_kwargs[name] = value
    return new_args, new_kwargs

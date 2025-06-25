from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import patch_function, on_import, before_modify_return, after


@before_modify_return
def my_func_wrapper(func, instance, args, kwargs):
    rv = func(*args, **kwargs)
    return rv + 1


@before_modify_return
def my_func_wrapper_2(func, instance, args, kwargs):
    rv = func(*args, **kwargs)
    return rv * 3


def test_no_patch():
    @on_import("aikido_zen.sinks.tests.utils.sample_module")
    def patch(m):
        pass  # Do nothing

    from aikido_zen.sinks.tests.utils.sample_module import my_func

    assert my_func(1) == 2
    assert my_func(2) == 3


def test_patch_happens_once():
    @on_import("aikido_zen.sinks.tests.utils.sample_module")
    def patch(m):
        patch_function(m, "my_func", my_func_wrapper)

    from aikido_zen.sinks.tests.utils.sample_module import my_func

    assert my_func(1) == 3
    assert my_func(2) == 4


def test_patch_happens_multiple():
    @on_import("aikido_zen.sinks.tests.utils.sample_module")
    def patch(m):
        patch_function(m, "my_func", my_func_wrapper)
        patch_function(m, "my_func", my_func_wrapper)
        patch_function(m, "my_func", my_func_wrapper)

    from aikido_zen.sinks.tests.utils.sample_module import my_func

    assert my_func(1) == 3
    assert my_func(2) == 4


def test_patch_happens_multiple_but_different_function():
    @on_import("aikido_zen.sinks.tests.utils.sample_module")
    def patch(m):
        patch_function(m, "my_func", my_func_wrapper)
        patch_function(m, "my_func", my_func_wrapper_2)

    from aikido_zen.sinks.tests.utils.sample_module import my_func

    assert my_func(1) == (1 + 2) * 3 == 9
    assert my_func(2) == (2 + 2) * 3 == 12


def test_patch_happens_multiple_but_different_order():
    @on_import("aikido_zen.sinks.tests.utils.sample_module")
    def patch(m):
        patch_function(m, "my_func", my_func_wrapper_2)
        patch_function(m, "my_func", my_func_wrapper)

    from aikido_zen.sinks.tests.utils.sample_module import my_func

    assert my_func(1) == (2 * 3) + 1 == 7
    assert my_func(2) == (3 * 3) + 1 == 10


def test_patch_happens_multiple_but_different_module():
    @on_import("aikido_zen.sinks.tests.utils.sample_module_2")
    def patch(m):
        patch_function(m, "my_func", my_func_wrapper)

    @on_import("aikido_zen.sinks.tests.utils.sample_module")
    def patch2(m):
        patch_function(m, "my_func", my_func_wrapper)

    from aikido_zen.sinks.tests.utils.sample_module_2 import my_func

    assert my_func(1) == 3
    assert my_func(2) == 4

from aikido_zen.sinks import on_import


def test_on_import_can_be_stacked():
    patched = []

    @on_import("os")
    @on_import("sys")
    def patch(module):
        patched.append(module.__name__)

    assert sorted(patched) == ["os", "sys"]
    assert patch is not None

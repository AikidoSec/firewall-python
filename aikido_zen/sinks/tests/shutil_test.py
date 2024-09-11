import pytest
from unittest.mock import patch
import aikido_zen.sinks.builtins
import aikido_zen.sinks.shutil


kind = "path_traversal"


def test_shutil_copyfile():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import shutil

        shutil.copyfile("Makefile", "test2")
        op = "builtins.open"
        args1 = ("Makefile",)
        args2 = ("test2",)
        assert len(mock_run_vulnerability_scan.call_args_list) == 2
        call_1 = mock_run_vulnerability_scan.call_args_list[0]
        call_2 = mock_run_vulnerability_scan.call_args_list[1]

        assert call_1.kwargs["op"] == call_2.kwargs["op"] == op
        assert call_1.kwargs["kind"] == call_2.kwargs["kind"] == kind
        assert call_1.kwargs["args"] == args1
        assert call_2.kwargs["args"] == args2


def test_shutil_copyfile():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import shutil

        shutil.copyfile(src="Makefile", dst="test2")
        op = "builtins.open"
        args1 = ("Makefile",)
        args2 = ("test2",)
        assert len(mock_run_vulnerability_scan.call_args_list) == 2
        call_1 = mock_run_vulnerability_scan.call_args_list[0]
        call_2 = mock_run_vulnerability_scan.call_args_list[1]

        assert call_1.kwargs["op"] == call_2.kwargs["op"] == op
        assert call_1.kwargs["kind"] == call_2.kwargs["kind"] == kind
        assert call_1.kwargs["args"] == args1
        assert call_2.kwargs["args"] == args2


def test_shutil_copymode():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import shutil

        shutil.copymode("Makefile", "test2")
        op = "shutil.copymode"
        args1 = ("Makefile",)
        args2 = ("test2",)
        assert len(mock_run_vulnerability_scan.call_args_list) == 3
        call_1 = mock_run_vulnerability_scan.call_args_list[0]
        call_2 = mock_run_vulnerability_scan.call_args_list[1]

        assert call_1.args == call_2.args == (kind, op)
        assert call_1.kwargs["args"] == args1
        assert call_2.kwargs["args"] == args2


def test_shutil_copystat():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import shutil

        shutil.copystat("Makefile", "test2")
        op = "shutil.copystat"
        args1 = ("Makefile",)
        args2 = ("test2",)
        assert len(mock_run_vulnerability_scan.call_args_list) == 3
        call_1 = mock_run_vulnerability_scan.call_args_list[0]
        call_2 = mock_run_vulnerability_scan.call_args_list[1]

        assert call_1.args == call_2.args == (kind, op)
        assert call_1.kwargs["args"] == args1
        assert call_2.kwargs["args"] == args2


def test_shutil_copytree():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import shutil

        with pytest.raises(NotADirectoryError):
            shutil.copytree("Makefile", "test2")
        op = "shutil.copytree"
        args1 = ("Makefile",)
        args2 = ("test2",)
        assert len(mock_run_vulnerability_scan.call_args_list) == 2
        call_1 = mock_run_vulnerability_scan.call_args_list[0]
        call_2 = mock_run_vulnerability_scan.call_args_list[1]

        assert call_1.args == call_2.args == (kind, op)
        assert call_1.kwargs["args"] == args1
        assert call_2.kwargs["args"] == args2


def test_shutil_move():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import shutil

        shutil.move("test2", "test3")
        op = "shutil.move"
        args1 = ("test2",)
        args2 = ("test3",)
        assert len(mock_run_vulnerability_scan.call_args_list) == 4
        call_1 = mock_run_vulnerability_scan.call_args_list[0]
        call_2 = mock_run_vulnerability_scan.call_args_list[1]

        assert call_1.args == call_2.args == (kind, op)
        assert call_1.kwargs["args"] == args1
        assert call_2.kwargs["args"] == args2


def test_shutil_copy():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import shutil

        shutil.copy("Makefile", "test2")
        op = "builtins.open"
        args1 = ("Makefile",)
        args2 = ("test2",)
        assert len(mock_run_vulnerability_scan.call_args_list) == 5
        call_1 = mock_run_vulnerability_scan.call_args_list[0]
        call_2 = mock_run_vulnerability_scan.call_args_list[1]

        assert call_1.kwargs["op"] == call_2.kwargs["op"] == op
        assert call_1.kwargs["kind"] == call_2.kwargs["kind"] == kind
        assert call_1.kwargs["args"] == args1
        assert call_2.kwargs["args"] == args2


def test_shutil_copy2():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import shutil

        shutil.copy2("Makefile", "test2")
        op = "builtins.open"
        args1 = ("Makefile",)
        args2 = ("test2",)
        assert len(mock_run_vulnerability_scan.call_args_list) == 5
        call_1 = mock_run_vulnerability_scan.call_args_list[0]
        call_2 = mock_run_vulnerability_scan.call_args_list[1]

        assert call_1.kwargs["op"] == call_2.kwargs["op"] == op
        assert call_1.kwargs["kind"] == call_2.kwargs["kind"] == kind
        assert call_1.kwargs["args"] == args1
        assert call_2.kwargs["args"] == args2


# Test that it can Handle all sorts of data :
def test_shutil_invalid_input():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import shutil

        op = "shutil.copystat"

        with pytest.raises(TypeError):
            shutil.copystat()
        mock_run_vulnerability_scan.assert_not_called()
        with pytest.raises(TypeError):
            shutil.copystat(123456789123456789)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called
        with pytest.raises(TypeError):
            shutil.copystat(None)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called
        with pytest.raises(TypeError):
            shutil.copystat(["list", "of", "commands"])
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test dictionary command
        with pytest.raises(TypeError):
            shutil.copystat({"key": "value"})
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            shutil.copystat(3.14)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test boolean command
        with pytest.raises(TypeError):
            shutil.copystat(True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test tuple command
        with pytest.raises(TypeError):
            shutil.copystat(("tuple", "command"))
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called


def test_rm_test_files():
    import os

    os.remove("test2")
    os.remove("test3")

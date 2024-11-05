import pytest
from unittest.mock import patch
import aikido_zen.sinks.builtins
from pathlib import Path, PurePath

kind = "path_traversal"
op = "builtins.open"


def test_open():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        with pytest.raises(FileNotFoundError):
            open("test_file")
        args = ("test_file",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)
        with pytest.raises(FileNotFoundError):
            open("")
        args = ("",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            open("ltlwtjl_tlnekt.py")
        args = ("ltlwtjl_tlnekt.py",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            open(b"afljqlqfefjq.py")
        args = (b"afljqlqfefjq.py",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        path = Path("./test", "/test.py")
        with pytest.raises(FileNotFoundError):
            open(path)
        args = (path,)
        # Need to use assert_any_call, since python 3.12 it uses os.path.join
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)

        path2 = PurePath("./test", "/test.py")
        with pytest.raises(FileNotFoundError):
            open(path2)
        args = (path2,)
        # Need to use assert_any_call, since python 3.12 it uses os.path.join
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)


def test_open_with_builtins_import():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import builtins

        with pytest.raises(FileNotFoundError):
            builtins.open("test_file")
        args = ("test_file",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)
        with pytest.raises(FileNotFoundError):
            builtins.open("")
        args = ("",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            builtins.open("ltlwtjl_tlnekt.py")
        args = ("ltlwtjl_tlnekt.py",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            builtins.open(b"shleklelkwge.py")
        args = (b"shleklelkwge.py",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_open_invalid_input():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        with pytest.raises(TypeError):
            open()
        mock_run_vulnerability_scan.assert_not_called()

        with pytest.raises(TypeError):
            open(123456789123456789)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            open(None)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            open(["list", "of", "commands"])
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test dictionary command
        with pytest.raises(TypeError):
            open({"key": "value"})
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            open(3.14)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test boolean command
        open(True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test tuple command
        with pytest.raises(TypeError):
            open(("tuple", "command"))
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

import pytest
from unittest.mock import patch
import aikido_zen.sinks.builtins
from pathlib import Path, PurePath

kind = "code_injection"


def test_eval():
    op = "builtins.eval"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        eval("lambda x: 67")
        args = "lambda x: 67"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        eval("print('Hello')")
        args = "print('Hello')"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_eval_with_builtins_import():
    op = "builtins.eval"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import builtins

        builtins.eval("8 + 9 + (3//2)")
        args = "8 + 9 + (3//2)"


def test_eval_invalid_input():
    op = "builtins.eval"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        with pytest.raises(TypeError):
            eval()
        mock_run_vulnerability_scan.assert_not_called()

        with pytest.raises(TypeError):
            eval(123456789123456789)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            eval(None)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            eval(["list", "of", "commands"])
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test dictionary command
        with pytest.raises(TypeError):
            eval({"key": "value"})
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            eval(3.14)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test tuple command
        with pytest.raises(TypeError):
            eval(("tuple", "command"))
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called


# Now also test exec :


def test_exec():
    op = "builtins.exec"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        exec("lambda y: (2+y)")
        args = "lambda y: (2+y)"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        exec("# Comment here")
        args = "# Comment here"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_exec_with_builtins_import():
    op = "builtins.exec"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import builtins

        builtins.exec("8 + 10 + (3//2)")
        args = "8 + 10 + (3//2)"


def test_exec_invalid_input():
    op = "builtins.exec"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        with pytest.raises(TypeError):
            exec()
        mock_run_vulnerability_scan.assert_not_called()

        with pytest.raises(TypeError):
            exec(123456789123456789)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            exec(None)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            exec(["list", "of", "commands"])
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test dictionary command
        with pytest.raises(TypeError):
            exec({"key": "value"})
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            exec(3.14)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test tuple command
        with pytest.raises(TypeError):
            exec(("tuple", "command"))
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

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
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


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
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


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


# Test compile(...) function :


def test_compile():
    op = "builtins.compile"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        compile("lambda y: (2+y)", "IDK", "exec")
        args = "lambda y: (2+y)"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        compile(b"lambda y: (3+y)", "IDK", "exec")
        args = "lambda y: (3+y)"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        compile("# Comment here", "IDK", "exec")
        args = "# Comment here"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        compile(b"# Comment here2", "IDK", "exec")
        args = "# Comment here2"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_compile_with_builtins_import():
    op = "builtins.compile"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import builtins

        builtins.compile("8 + 10 + (3//2)", "IDK", "exec")
        args = "8 + 10 + (3//2)"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        builtins.compile(b"8 + 11 + (3//2)", "IDK", "exec")
        args = "8 + 11 + (3//2)"
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_compile_invalid_input():
    op = "builtins.compile"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        with pytest.raises(TypeError):
            compile()
        mock_run_vulnerability_scan.assert_not_called()

        with pytest.raises(TypeError):
            compile(123456789123456789, "IDK", "exec")
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            compile(None, "IDK", "exec")
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            compile(["list", "of", "commands"], "IDK", "exec")
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test dictionary command
        with pytest.raises(TypeError):
            compile({"key": "value"}, "IDK", "exec")
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            compile(3.14, "IDK", "exec")
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test tuple command
        with pytest.raises(TypeError):
            compile(("tuple", "command"), "IDK", "exec")
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

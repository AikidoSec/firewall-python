import pytest
from unittest.mock import patch
import aikido_zen.sinks.subprocess

kind = "shell_injection"


def test_subprocess_call():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.Popen"

        subprocess.call(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        subprocess.call(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        subprocess.call("ls -la", shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_subprocess_call_not_called():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        subprocess.call(["ls", "-la"])

        subprocess.call(["pwd"], shell=False)

        subprocess.call("ls")

        # Make sure there is no call regarding shell injection:
        assert (
            list(filter(is_shell_injection, mock_run_vulnerability_scan.call_args_list))
            == []
        )


def test_subprocess_run():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.Popen"

        subprocess.run(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        subprocess.run(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_subprocess_run_not_called():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        subprocess.run(["ls", "-la"])

        subprocess.run(["pwd"], shell=False)

        # Make sure there is no call regarding shell injection:
        assert (
            list(filter(is_shell_injection, mock_run_vulnerability_scan.call_args_list))
            == []
        )


def test_subprocess_check_call():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.Popen"

        subprocess.check_call(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_call(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_subprocess_check_call_not_called():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        subprocess.check_call(["ls", "-la"], shell=False)

        subprocess.check_call(["whoami"])

        # Make sure there is no call regarding shell injection:
        assert (
            list(filter(is_shell_injection, mock_run_vulnerability_scan.call_args_list))
            == []
        )


def test_subprocess_popen():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.Popen"

        subprocess.Popen(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        subprocess.Popen(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        subprocess.Popen("ls -la", shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        process = subprocess.Popen(args="ls -la", shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        process.kill()  # Test class functions
        process.pid  # Access a class attribute


def test_subprocess_popen_not_called():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        subprocess.Popen(["ls", "-la"])

        subprocess.Popen(["whoami"], shell=False)

        subprocess.Popen("pwd", shell=False)

        subprocess.Popen(args="pwd", shell=False)

        subprocess.Popen(args="pwd")

        # Make sure there is no call regarding shell injection:
        assert (
            list(filter(is_shell_injection, mock_run_vulnerability_scan.call_args_list))
            == []
        )


def test_subprocess_check_output():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.check_output"

        subprocess.check_output(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_output(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_output(("tuple", "command"), shell=True)
        args = ("tuple command",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_output({"key": "value"}, shell=True)
        args = ("key",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_output({"ke": "value", "key2": "value2"}, shell=True)
        args = ("ke key2",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_subprocess_check_output():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        subprocess.check_output(["ls", "-la"], shell=False)

        with pytest.raises(FileNotFoundError):
            subprocess.check_output(["cfsknflks"])

        with pytest.raises(FileNotFoundError):
            subprocess.check_output(("tuple", "command"), shell=False)

        with pytest.raises(FileNotFoundError):
            subprocess.check_output({"key": "value"})

        with pytest.raises(FileNotFoundError):
            subprocess.check_output({"ke": "value", "key2": "value2"}, shell=False)

        # Make sure there is no call regarding shell injection:
        assert (
            list(filter(is_shell_injection, mock_run_vulnerability_scan.call_args_list))
            == []
        )


def test_subprocess_invalid_input():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.call"
        with pytest.raises(TypeError):
            subprocess.call(shell=True)
        mock_run_vulnerability_scan.assert_not_called()

        with pytest.raises(TypeError):
            subprocess.call(123456789123456789, shell=True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            subprocess.call(None, shell=True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            subprocess.call(3.14, shell=True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test boolean command
        with pytest.raises(TypeError):
            subprocess.call(True, shell=True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called


def is_shell_injection(args):
    return args[1]["kind"] == "shell_injection"

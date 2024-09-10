import pytest
from unittest.mock import patch
import aikido_zen.sinks.io


kind = "path_traversal"


def test_io_open():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import io

        io.open("Makefile", mode="a")
        op = "io.open"
        args1 = ("Makefile",)
        mock_run_vulnerability_scan.assert_called_once_with(
            kind=kind, op=op, args=args1
        )


def test_io_open_2():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import io

        io.open("./Makefile", mode="a")
        op = "io.open"
        args1 = ("./Makefile",)
        mock_run_vulnerability_scan.assert_called_once_with(
            kind=kind, op=op, args=args1
        )


def test_io_open_3():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import io

        io.open("/etc/hosts", mode="r")
        op = "io.open"
        args1 = ("/etc/hosts",)
        mock_run_vulnerability_scan.assert_called_once_with(
            kind=kind, op=op, args=args1
        )


def test_io_open_code():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import io

        io.open_code("Makefile")
        op = "io.open_code"
        args1 = ("Makefile",)
        mock_run_vulnerability_scan.assert_called_once_with(
            kind=kind, op=op, args=args1
        )


def test_io_open_code_2():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import io

        io.open_code("./Makefile")
        op = "io.open_code"
        args1 = ("./Makefile",)
        mock_run_vulnerability_scan.assert_called_once_with(
            kind=kind, op=op, args=args1
        )


def test_io_open_code_3():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import io

        io.open_code("/etc/hosts")
        op = "io.open_code"
        args1 = ("/etc/hosts",)
        mock_run_vulnerability_scan.assert_called_once_with(
            kind=kind, op=op, args=args1
        )

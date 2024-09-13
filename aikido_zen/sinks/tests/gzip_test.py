import pytest
from unittest.mock import patch
import aikido_zen.sinks.builtins

kind = "path_traversal"


def test_gzip_gzipfile():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import gzip

        with pytest.raises(FileNotFoundError):
            gzip.GzipFile("sdnklsdnlkvsv.gz")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("sdnklsdnlkvsv.gz",)
        )

        with pytest.raises(FileNotFoundError):
            gzip.GzipFile(filename="jsgljlskjglkds.gz")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("jsgljlskjglkds.gz",)
        )

        with pytest.raises(FileNotFoundError):
            gzip.GzipFile(filename="/kjtkl.gz")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("/kjtkl.gz",)
        )


def test_gzip_open():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import gzip

        with pytest.raises(FileNotFoundError):
            gzip.open("sgsglksjks.gz")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("sgsglksjks.gz",)
        )

        with pytest.raises(FileNotFoundError):
            gzip.open(filename="qjrpoiuzu.gz")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("qjrpoiuzu.gz",)
        )

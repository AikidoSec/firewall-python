import pytest
from unittest.mock import patch
import aikido_zen.sinks.builtins

kind = "path_traversal"


def test_lzma_lzmafile():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import lzma

        with pytest.raises(FileNotFoundError):
            lzma.LZMAFile("sdnklsdnlkvsv.lzma")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("sdnklsdnlkvsv.lzma",)
        )

        with pytest.raises(FileNotFoundError):
            lzma.LZMAFile(filename="jsgljlskjglkds.lzma")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("jsgljlskjglkds.lzma",)
        )

        with pytest.raises(FileNotFoundError):
            lzma.LZMAFile(filename="/kjtkl.lzma")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("/kjtkl.lzma",)
        )


def test_lzma_open():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import lzma

        with pytest.raises(FileNotFoundError):
            lzma.open("sgsglksjks.lzma")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("sgsglksjks.lzma",)
        )

        with pytest.raises(FileNotFoundError):
            lzma.open(filename="qjrpoiuzu.lzma")
        mock_run_vulnerability_scan.assert_called_with(
            kind="path_traversal", op="builtins.open", args=("qjrpoiuzu.lzma",)
        )

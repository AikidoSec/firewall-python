import pytest
from unittest.mock import patch
import aikido_firewall.sinks.os

kind = "path_traversal"


def test_ospath_commands():
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        os.path.realpath("test/test2")
        op = "os.path.realpath"
        args = ("test/test2",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.path.getsize("aqkqjefbkqlleq_qkvfjksaicuaviel")
            op = "os.path.getsize"
            args = ("aqkqjefbkqlleq_qkvfjksaicuaviel",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_os_commands():
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        os.access(".xyzxyz", 0)
        op = "os.access"
        args = (".xyzxyz",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.chmod("1234567", 0)
            op = "os.chmod"
            args = ("1234567",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.chown("fLKEFLKENGKWBGKJEBLKALKKnkjfkj_jefkjwbgkjrw", 0)
            op = "os.chown"
            args = ("fLKEFLKENGKWBGKJEBLKALKKnkjfkj_jefkjwbgkjrw",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.mkdir("qlkgkjbnlzheioe_kjbfkjeiLJ", 0)
            op = "os.mkdir"
            args = ("qlkgkjbnlzheioe_kjbfkjeiLJ",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.listdir("TEST_PATH_test")
            op = "os.listdir"
            args = ("TEST_PATH_test",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.readlink("Pathy_jgyr138")
            op = "os.readlink"
            args = ("Pathy_jgyr138",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.unlink("test_path.pathy")
            op = "os.unlink"
            args = ("test_path.pathy",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.rename("sjkvabprvqfwqjkl_kwfkjbfqhjfq")
            op = "os.rename"
            args = ("sjkvabprvqfwqjkl_kwfkjbfqhjfq",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.rmdir("wkoiropwejbvisvfkl_lhfebqljfebjqklfe")
            op = "os.rmdir"
            args = ("wkoiropwejbvisvfkl_lhfebqljfebjqklfe",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.remove("wlhgiwhgpowjfoiljfe_lkqfqkjjknclOIA")
            op = "os.remove"
            args = ("wlhgiwhgpowjfoiljfe_lkqfqkjjknclOIA",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.symlink("fqppnfqdbsklclfkn_lqbfjqbkwnd")
            op = "os.symlink"
            args = ("fqppnfqdbsklclfkn_lqbfjqbkwnd",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.link("qkfhwifqqlejfke_qlfjboqvdbshjw")
            op = "os.link"
            args = ("qkfhwifqqlejfke_qlfjboqvdbshjw",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.makedirs("nksnvkqnvlkenleqknl_lkwnflqkwndqle")
            op = "os.makedirs"
            args = ("nksnvkqnvlkenleqknl_lkwnflqkwndqle",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

            os.walk("qlfjwqqfqelfknef_kwlkgrlkbwkalwd")
            op = "os.walk"
            args = ("qlfjwqqfqelfknef_kwlkgrlkbwkalwd",)
            mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

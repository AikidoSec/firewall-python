import pytest
from pathlib import Path, PurePath
from unittest.mock import patch
import aikido_zen.sinks.os

kind = "path_traversal"


def test_ospath_commands():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        os.path.realpath("test/test2")
        op = "os.path.join"
        args = ("test/test2",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.path.getsize("aqkqjefbkqlleq_qkvfjksaicuaviel")
        op = "os.path.getsize"
        args = ("aqkqjefbkqlleq_qkvfjksaicuaviel",)
        # Need to use assert_any_call, since python 3.12 it uses os.path.join
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)

        os.path.realpath(b"te2st/test2")
        op = "os.path.join"
        args = (b"te2st/test2",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        path1 = Path("./", "../", "test/../test2")
        with pytest.raises(FileNotFoundError):
            os.path.getsize(path1)

        op = "os.path.getsize"
        args = (path1,)
        # Need to use assert_any_call, since python 3.12 it uses os.path.join
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)


def test_ospath_command_absolute_path():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        os.path.abspath("../test/test2")
        op = "os.path.join"
        args = ("../test/test2",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        path1 = Path("./test", "test2", "test3")
        os.path.abspath(path1)

        op = "os.path.join"
        args = ("test/test2/test3",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_ospath_expanduser():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        os.path.expanduser("../test/test2")
        op = "os.path.expanduser"
        args = ("../test/test2",)
        # Need to use assert_any_call, since python 3.12 it uses os.path.join
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)

        path1 = Path("./test", "test2", "test3")
        os.path.expanduser(path1)

        op = "os.path.expanduser"
        args = (path1,)
        # Need to use assert_any_call, since python 3.12 it uses os.path.join
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)


def test_ospath_expandvars():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        os.path.expandvars("../test/test2")
        op = "os.path.expandvars"
        args = ("../test/test2",)
        # Need to use assert_any_call, since python 3.12 it uses os.path.join
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)

        path1 = Path("./test", "test2", "test3")
        os.path.expandvars(path1)

        op = "os.path.expandvars"
        args = (path1,)
        # Need to use assert_any_call, since python 3.12 it uses os.path.join
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)


def test_ospath_join():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        os.path.join("../", "/etc/passwd", "..")
        op = "os.path.join"
        args1 = ("../",)
        args2 = ("/etc/passwd",)
        args3 = ("..",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args1)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args2)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args3)


@patch("aikido_zen.vulnerabilities.run_vulnerability_scan")
def test_ospath_join_bytes(mock_run_vulnerability_scan):
    import os

    op = "os.path.join"

    # Test with bytes arguments
    os.path.join(b"../", b"/etc/passwd", b"..")
    args1 = (b"../",)
    args2 = (b"/etc/passwd",)
    args3 = (b"..",)

    mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args1)
    mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args2)
    mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args3)


@patch("aikido_zen.vulnerabilities.run_vulnerability_scan")
def test_ospath_join_path_objects(mock_run_vulnerability_scan):
    import os

    op = "os.path.join"

    # Test with Path objects
    os.path.join(Path("../"), Path("/etc/passwd"), Path(".."))
    args1 = (Path("../"),)
    args2 = (Path("/etc/passwd"),)
    args3 = (Path(".."),)

    mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args1)
    mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args2)
    mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args3)


@patch("aikido_zen.vulnerabilities.run_vulnerability_scan")
def test_ospath_join_mixed_paths(mock_run_vulnerability_scan):
    import os

    op = "os.path.join"

    # Test with mixed strings and Path objects
    os.path.join("../", Path("/etc/passwd"), "..")
    args1 = ("../",)
    args2 = (Path("/etc/passwd"),)
    args3 = ("..",)

    mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args1)
    mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args2)
    mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args3)


def test_os_commands():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
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

        with pytest.raises(FileNotFoundError):
            os.chown("fLKEFLKENGKWBGKJEBLKALKKnkjfkj_jefkjwbgkjrw", 0, 0)
        op = "os.chown"
        args = ("fLKEFLKENGKWBGKJEBLKALKKnkjfkj_jefkjwbgkjrw",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        os.mkdir("qlkgkjbnlzheioe_kjbfkjeiLJ", 0)
        op = "os.mkdir"
        args = ("qlkgkjbnlzheioe_kjbfkjeiLJ",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.listdir("TEST_PATH_test")
        op = "os.listdir"
        args = ("TEST_PATH_test",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.readlink("Pathy_jgyr138")
        op = "os.readlink"
        args = ("Pathy_jgyr138",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.unlink("test_path.pathy")
        op = "os.unlink"
        args = ("test_path.pathy",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.unlink(b"wjlewjrlke")
        op = "os.unlink"
        args = (b"wjlewjrlke",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        os.rename("qlkgkjbnlzheioe_kjbfkjeiLJ", "lkflkenlnlgksnk_aknflkenfk")
        op = "os.rename"
        args = ("qlkgkjbnlzheioe_kjbfkjeiLJ",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)
        args = ("lkflkenlnlgksnk_aknflkenfk",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.rename(b"akflaflkqkajlqjoiq", b"kfjlfehfkakj")
        op = "os.rename"
        args = (b"akflaflkqkajlqjoiq",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)
        args = (b"kfjlfehfkakj",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.rename("akflaflkqkajlqjoiq", b"aflkkelwwgw")
        op = "os.rename"
        args = ("akflaflkqkajlqjoiq",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)
        args = (b"aflkkelwwgw",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)

        os.rmdir("lkflkenlnlgksnk_aknflkenfk")
        op = "os.rmdir"
        args = ("lkflkenlnlgksnk_aknflkenfk",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.remove("qlkgkjbnlzheioe_kjbfkjeiLJ")
        op = "os.remove"
        args = ("qlkgkjbnlzheioe_kjbfkjeiLJ",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        os.symlink("fqppnfqdbsklclfkn_lqbfjqbkwnd", "aqwfkjqkjqwfhoie_kjfhejlwqk")
        op = "os.symlink"
        args = ("fqppnfqdbsklclfkn_lqbfjqbkwnd",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)
        args = ("aqwfkjqkjqwfhoie_kjfhejlwqk",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)
        os.remove("aqwfkjqkjqwfhoie_kjfhejlwqk")

        path1 = PurePath("kkjehrqlknl_qk3rqlrjgna")
        with pytest.raises(FileNotFoundError):
            os.link("qkfhwifqqlejfke_qlfjboqvdbshjw", path1)
        op = "os.link"
        args = ("qkfhwifqqlejfke_qlfjboqvdbshjw",)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)
        args = (path1,)
        mock_run_vulnerability_scan.assert_any_call(kind=kind, op=op, args=args)

        os.walk("qlfjwqqfqelfknef_kwlkgrlkbwkalwd")
        op = "os.walk"
        args = ("qlfjwqqfqelfknef_kwlkgrlkbwkalwd",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(FileNotFoundError):
            os.open("gmlwgewlnqlfnawglkwnfleknlew", os.O_RDONLY)
        op = "os.open"
        args = ("gmlwgewlnqlfnawglkwnfleknlew",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


# Test that it can Handle all sorts of data :
def test_os_invalid_input():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        op = "os.link"

        with pytest.raises(TypeError):
            os.link()
        mock_run_vulnerability_scan.assert_not_called()
        with pytest.raises(TypeError):
            os.link(123456789123456789)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called
        with pytest.raises(TypeError):
            os.link(None)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called
        with pytest.raises(TypeError):
            os.link(["list", "of", "commands"])
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test dictionary command
        with pytest.raises(TypeError):
            os.link({"key": "value"})
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            os.link(3.14)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test boolean command
        with pytest.raises(TypeError):
            os.link(True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test tuple command
        with pytest.raises(TypeError):
            os.link(("tuple", "command"))
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called


# Test that it can Handle all sorts of data :
def test_ospath_invalid_input():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        op = "os.path.realpath"

        with pytest.raises(TypeError):
            os.path.realpath()
        mock_run_vulnerability_scan.assert_not_called()
        with pytest.raises(TypeError):
            os.path.realpath(123456789123456789)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called
        with pytest.raises(TypeError):
            os.path.realpath(None)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called
        with pytest.raises(TypeError):
            os.path.realpath(["list", "of", "commands"])
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test dictionary command
        with pytest.raises(TypeError):
            os.path.realpath({"key": "value"})
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            os.path.realpath(3.14)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test boolean command
        with pytest.raises(TypeError):
            os.path.realpath(True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test tuple command
        with pytest.raises(TypeError):
            os.path.realpath(("tuple", "command"))
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

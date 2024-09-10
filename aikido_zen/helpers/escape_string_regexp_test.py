import re
import pytest
from aikido_zen.helpers import escape_string_regexp


def test_escape_string_regexp():
    assert (
        escape_string_regexp("\\ ^ $ * + ? . ( ) | { } [ ]")
        == "\\\\ \\^ \\$ \\* \\+ \\? \\. \\( \\) \\| \\{ \\} \\[ \\]"
    )


def test_escape_hyphen_pcre():
    assert escape_string_regexp("foo - bar") == "foo \\x2d bar"


def test_escape_hyphen_unicode_flag():
    assert re.match(escape_string_regexp("-"), "-u") is not None

"""Exports the contains_shell_syntax function"""

import regex as re

# Constants
dangerous_chars = [
    "#",
    "!",
    '"',
    "$",
    "&",
    "'",
    "(",
    ")",
    "*",
    ";",
    "<",
    "=",
    ">",
    "?",
    "[",
    "\\",
    "]",
    "^",
    "`",
    "{",
    "|",
    "}",
    " ",
    "\n",
    "\t",
    "~",
]

commands = [
    "sleep",
    "shutdown",
    "reboot",
    "poweroff",
    "halt",
    "ifconfig",
    "chmod",
    "chown",
    "ping",
    "ssh",
    "scp",
    "curl",
    "wget",
    "telnet",
    "kill",
    "killall",
    "rm",
    "mv",
    "cp",
    "touch",
    "echo",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "awk",
    "sed",
    "sort",
    "uniq",
    "wc",
    "ls",
    "env",
    "ps",
    "who",
    "whoami",
    "id",
    "w",
    "df",
    "du",
    "pwd",
    "uname",
    "hostname",
    "netstat",
    "passwd",
    "arch",
    "printenv",
    "logname",
    "pstree",
    "hostnamectl",
    "set",
    "lsattr",
    "killall5",
    "dmesg",
    "history",
    "free",
    "uptime",
    "finger",
    "top",
    "shopt",
    ":",  # Colon is a null command
]

path_prefixes = [
    "/bin/",
    "/sbin/",
    "/usr/bin/",
    "/usr/sbin/",
    "/usr/local/bin/",
    "/usr/local/sbin/",
]

separators = [" ", "\t", "\n", ";", "&", "|", "(", ")", "<", ">"]


# Function to sort commands by length (longer commands first)
def by_length(a, b):
    """Sort by length desc"""
    return len(b) - len(a)


# Create the regex pattern
commands_regex = re.compile(
    r"([/.]*("
    + "|".join(map(re.escape, path_prefixes))
    + r")?("
    + "|".join(sorted(commands, key=len, reverse=True))
    + r"))",
    re.I | re.M,
)


def contains_shell_syntax(command, user_input):
    """
    Checks if the user input contains shell syntax given the command
    """
    if user_input.isspace():
        # The entire user input is just whitespace, ignore
        return False

    if any(c in user_input for c in dangerous_chars):
        return True

    # The command is the same as the user input
    # Rare case, but it's possible
    # e.g. command is `shutdown` and user input is `shutdown`
    # (`shutdown -h now` will be caught by the dangerous chars as it contains a space)
    if command == user_input:
        match = commands_regex.match(command)
        return match is not None and match.start() == 0 and match.end() == len(command)

    # Check if the command contains a commonly used command
    for match in commands_regex.finditer(command):
        # We found a command like `rm` or `/sbin/shutdown` in the command
        # Check if the command is the same as the user input
        # If it's not the same, continue searching
        if user_input != match[0]:
            continue

        # Otherwise, we'll check if the command is surrounded by separators
        # These separators are used to separate commands and arguments
        # e.g. `rm<space>-rf`
        # e.g. `ls<newline>whoami`
        # e.g. `echo<tab>hello`
        char_before = command[match.start() - 1] if match.start() > 0 else None
        char_after = command[match.end()] if match.end() < len(command) else None

        # Check surrounding characters
        if char_before in separators and char_after in separators:
            #  e.g. `<separator>rm<separator>`
            return True
        if char_before in separators and char_after is None:
            #  e.g. `<separator>rm`
            return True
        if char_before is None and char_after in separators:
            # e.g. `rm<separator>`
            return True
    return False

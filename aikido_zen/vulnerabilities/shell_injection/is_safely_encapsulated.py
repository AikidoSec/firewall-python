"""
Exports the is_safely_encapsulated function
"""

escape_chars = ['"', "'"]
dangerous_chars_inside_double_quotes = ["$", "`", "\\", "!"]


def _parse_shell_quoting_state(command, user_input_start, user_input_end):
    """
    Parse the shell quoting state at the position where user_input appears.
    Returns the active quote character ('"', "'", or None) at the start of user_input.

    This function walks through the command character by character, tracking
    which quote context is active, to determine if user_input is truly
    encapsulated in quotes.
    """
    quote_state = None  # None, '"', or "'"
    i = 0

    while i < user_input_start:
        char = command[i]

        if quote_state is None:
            # Not inside any quotes
            if char == '"':
                quote_state = '"'
            elif char == "'":
                quote_state = "'"
        elif quote_state == '"':
            # Inside double quotes
            if char == "\\" and i + 1 < len(command):
                # Backslash escapes the next character in double quotes
                i += 1  # Skip the next character
            elif char == '"':
                quote_state = None
        elif quote_state == "'":
            # Inside single quotes - nothing escapes except closing single quote
            if char == "'":
                quote_state = None

        i += 1

    return quote_state


def is_safely_encapsulated(command, user_input):
    """Checks if the user input is safely encapsulated inside the command"""
    if not user_input or user_input not in command:
        return True

    # Find all occurrences of user_input in command
    start_index = 0
    all_safe = True

    while True:
        pos = command.find(user_input, start_index)
        if pos == -1:
            break

        user_input_start = pos
        user_input_end = pos + len(user_input)

        # Parse the shell quoting state at this position
        quote_state = _parse_shell_quoting_state(
            command, user_input_start, user_input_end
        )

        # Check if the user input is safely encapsulated
        if quote_state is None:
            # Not inside any quotes - not safe
            all_safe = False
            break
        elif quote_state == "'":
            # Inside single quotes - safe (nothing is interpreted)
            # But check if the user input contains the quote character itself
            if "'" in user_input:
                all_safe = False
                break
        elif quote_state == '"':
            # Inside double quotes - only safe if no dangerous characters
            if any(char in user_input for char in dangerous_chars_inside_double_quotes):
                all_safe = False
                break

        start_index = user_input_end

    return all_safe

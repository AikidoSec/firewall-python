"""
Helper function file, see function definition for more info
"""


def get_current_and_next_segments(array):
    """Get the current and next segments of an array"""
    return [(array[i], array[i + 1]) for i in range(len(array) - 1)]

"""
Helper function file, see function docstring
"""


def limit_length_metadata(metadata, max_length):
    """
    Limits the length of the metadata obj so it can be sent out
    """
    for key in metadata:
        if len(metadata[key]) > max_length:
            metadata[key] = metadata[key][:max_length]

    return metadata

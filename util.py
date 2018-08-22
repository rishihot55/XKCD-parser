"""A set of basic util functions used in the script."""
from itertools import repeat
import sys
import os


def prefix(prefix_str, iterable):
    """Apply a string prefix to the iterable."""
    return map(lambda p, x: p + str(x), repeat(prefix_str), iterable)


def error(*args, **kwargs):
    """Print to STDERR."""
    print(*args, file=sys.stderr, **kwargs)


def safemkdir(directory):
    """Create a directory if one does not exist already."""
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_contents_to_path(data, path):
    """Write data to a file in the path."""
    with open(path, 'wb') as file:
        file.write(data)


def yes_no_prompt(text):
    """Create a yes no prompt which takes yes by default."""
    yes_values = ["Y", "y", ""]
    input_text = input(text + " [Y/n]")
    return input_text in yes_values

"""
A module to define helper functions for paths.
"""

import os


def make_path_absolute(path):
    """
    Makes a relative path absolute, using the directory of this python file as parent folder.
    (This used to be useful as long as this file was next to the main python file. But it does
    not seem to useful any more, now that it's part of the utils package...)
    """
    if path and not os.path.isabs(path):
        # we assume that relative paths are relative to the script directory, not to the current
        # working directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.normpath(os.path.join(script_dir, path))
    return path

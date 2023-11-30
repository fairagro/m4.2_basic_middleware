import os

def make_path_absolute(path):
    if path and not os.path.isabs(path):
        # we assume that relative paths are relative to the script directory, not to the current working directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.normpath(os.path.join(script_dir, path))
    return path
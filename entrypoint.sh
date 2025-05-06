#!/bin/sh
set -e

# Allow Git to work in the mounted output directory
# This cannot be done from within python code, as GitPython cannot set global
# config items.
git config --global --add safe.directory /middleware/output

# Run your app logic
exec "$@"

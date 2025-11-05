#!/bin/sh

# Publish script for miseqinteropreader
# Usage: ./scripts/publish.sh

set -eu  # Exit on error and undefined variables

# Check requirements
test -f "pyproject.toml" || { echo "Error: pyproject.toml not found"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "Error: uv not installed"; exit 1; }
test -n "${MISEQINTEROPREADER_PYPI_TOKEN-}" || { echo "Error: MISEQINTEROPREADER_PYPI_TOKEN not set"; exit 1; }

# Clean and build
rm -rf dist/ build/ *.egg-info
uv build

# Publish
uv publish --token "$MISEQINTEROPREADER_PYPI_TOKEN"

echo "Published to PyPI: https://pypi.org/project/miseqinteropreader/"

#!/bin/sh

# Publish script for miseqinteropreader
# Usage: ./scripts/publish.sh

set -eu  # Exit on error and undefined variables

# Check requirements
test -f "pyproject.toml" || { echo "Error: pyproject.toml not found"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "Error: uv not installed"; exit 1; }
test -n "${MISEQINTEROPREADER_PYPI_TOKEN-}" || { echo "Error: MISEQINTEROPREADER_PYPI_TOKEN not set"; exit 1; }

# Check that we're on a git tag (required for proper versioning)
if ! git describe --tags --exact-match >/dev/null 2>&1; then
    echo "Error: Not on a git tag. PyPI requires a clean version."
    echo "Current version would be: $(git describe --tags --always)"
    echo "Create a tag first: git tag v0.1.0 && git push origin v0.1.0"
    exit 1
fi

# Build and publish
uv build
uv publish --token "$MISEQINTEROPREADER_PYPI_TOKEN"

echo "Published to PyPI: https://pypi.org/project/miseqinteropreader/"

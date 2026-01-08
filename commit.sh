#!/bin/bash
# Helper script to commit with pre-commit hooks
# This runs pre-commit first, stages any changes, then commits

set -e

# Run pre-commit on all files first
echo "Running pre-commit hooks..."
pre-commit run --all-files

# Stage any changes made by pre-commit
echo "Staging changes made by pre-commit..."
git add -A

# If there are staged changes, show them
if ! git diff --cached --quiet; then
    echo "Changes to be committed:"
    git diff --cached --stat
    echo ""
    echo "Ready to commit. Run: git commit -m 'Your message'"
else
    echo "No changes to commit."
fi

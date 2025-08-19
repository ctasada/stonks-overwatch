#!/bin/bash
set -euo pipefail

# Run pre-commit autoupdate
echo "Running pre-commit autoupdate..."
pre-commit autoupdate

# Check if there are changes to .pre-commit-config.yaml
git add .pre-commit-config.yaml
if ! git diff --cached --quiet; then
  echo "pre-commit config updated. Committing changes."
  git config user.name "github-actions[bot]"
  git config user.email "github-actions[bot]@users.noreply.github.com"
  git commit -m "chore: autoupdate pre-commit hooks"
else
  echo "No changes to pre-commit config."
fi

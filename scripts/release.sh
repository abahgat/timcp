#!/bin/bash
set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
  echo "Error: Working directory is not clean. Please commit or stash changes."
  exit 1
fi

# Function to get current version
get_version() {
  grep -m1 'version = "' pyproject.toml | cut -d'"' -f2
}

CURRENT_VERSION=$(get_version)
echo "Current version: $CURRENT_VERSION"

# Ask for new version
read -p "Enter new version (e.g., 1.0.0): " NEW_VERSION

if [[ -z "$NEW_VERSION" ]]; then
  echo "Error: Version cannot be empty."
  exit 1
fi

if [[ "$NEW_VERSION" == "$CURRENT_VERSION" ]]; then
  echo "Error: New version must be different from current version."
  exit 1
fi

# Update pyproject.toml (works on Linux/macOS)
# Using python to strictly replace the version in the [project] table would be better,
# but for simplicity/universality with standard tools, we'll use sed carefully.
# We match 'version = "..."' only.
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
else
  sed -i "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
fi

echo "Updated pyproject.toml to version $NEW_VERSION"

# Confirm action
read -p "Ready to commit, tag v$NEW_VERSION, and push? (y/N) " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Aborted. Please revert changes to pyproject.toml manually if needed."
  exit 0
fi

# Git operations
git add pyproject.toml
git commit -m "chore: release v$NEW_VERSION"
git tag "v$NEW_VERSION"

echo "Pushing commit and tag..."
git push origin main
git push origin "v$NEW_VERSION"

echo "Done! The release workflow should now be running on GitHub."
echo "Check progress here: https://github.com/$(gh repo view --json owner,name --template '{{.owner.login}}/{{.name}}')/actions"

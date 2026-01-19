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

# Update pyproject.toml using Python for cross-platform compatibility
python3 -c "
import sys

current_version = '$CURRENT_VERSION'
new_version = '$NEW_VERSION'
file_path = 'pyproject.toml'

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
inside_project = False
replaced = False

for line in lines:
    stripped = line.strip()
    if stripped == '[project]':
        inside_project = True
    elif stripped.startswith('[') and stripped != '[project]':
        inside_project = False

    if inside_project and line.startswith('version = ') and current_version in line:
        new_lines.append(f'version = \"{new_version}\"\n')
        replaced = True
    else:
        new_lines.append(line)

if not replaced:
    print(f'Error: Could not find version string \"{current_version}\" inside [project] block.')
    sys.exit(1)

with open(file_path, 'w') as f:
    f.writelines(new_lines)
"

if [[ $? -ne 0 ]]; then
    echo "Failed to update pyproject.toml"
    exit 1
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

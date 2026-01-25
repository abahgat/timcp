#!/usr/bin/env python3
import sys
import argparse
import json
import os


def bump_version(current_version, new_version, file_path="pyproject.toml"):
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    new_lines = []
    inside_project = False
    replaced = False

    for line in lines:
        stripped = line.strip()
        if stripped == "[project]":
            inside_project = True
        elif stripped.startswith("[") and stripped != "[project]":
            inside_project = False

        if (
            inside_project
            and line.startswith("version = ")
            and f'"{current_version}"' in line
        ):
            new_lines.append(f'version = "{new_version}"\n')
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        print(
            f'Error: Could not find version string "{current_version}" inside [project] block in {file_path}.'
        )
        sys.exit(1)

    with open(file_path, "w") as f:
        f.writelines(new_lines)

    print(f"Successfully bumped version from {current_version} to {new_version}")


def update_server_json(new_version, file_path="server.json"):
    if not os.path.exists(file_path):
        return

    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        data["version"] = new_version
        if "packages" in data and isinstance(data["packages"], list):
            for pkg in data["packages"]:
                if isinstance(pkg, dict):
                    pkg["version"] = new_version

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"Successfully bumped version in {file_path} to {new_version}")
    except Exception as e:
        print(f"Warning: Failed to update {file_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bump version in pyproject.toml")
    parser.add_argument("current_version", help="Current version string")
    parser.add_argument("new_version", help="New version string")

    args = parser.parse_args()
    bump_version(args.current_version, args.new_version)
    update_server_json(args.new_version)

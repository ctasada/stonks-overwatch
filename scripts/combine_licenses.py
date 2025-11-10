#!/usr/bin/env python3
"""Script to combine NodeJS licenses into THIRD_PARTY_LICENSES.txt file."""

import json
import sys
from pathlib import Path


def main():
    """Combine NodeJS licenses with Python licenses."""
    try:
        # Read the NodeJS licenses JSON
        with open("npm-licenses.json", "r") as f:
            data = json.load(f)

        # Append NodeJS licenses to the file
        with open("THIRD_PARTY_LICENSES.txt", "a") as f:
            for pkg, info in sorted(data.items()):
                # Parse package name and version
                # Handle scoped packages like @seahsky/chartjs-plugin-autocolors@0.2.6
                if pkg.startswith("@"):
                    # For scoped packages: @scope/name@version
                    parts = pkg.split("@")
                    name = "@" + parts[1]
                    version = parts[2] if len(parts) > 2 else "unknown"
                else:
                    # For regular packages: name@version
                    parts = pkg.rsplit("@", 1)
                    name = parts[0]
                    version = parts[1] if len(parts) > 1 else "unknown"

                # Write package info
                f.write(name + "\n")
                f.write(version + "\n")
                f.write(info.get("licenses", "UNKNOWN") + "\n")

                # Write license text
                license_file = info.get("licenseFile")
                if license_file:
                    # Prepend 'src/' to the relative path since we're running from root
                    license_path = Path("src") / license_file
                    try:
                        with open(license_path, "r", encoding="utf-8", errors="ignore") as lf:
                            f.write(lf.read())
                    except Exception as e:
                        f.write(f"License text not available (Error: {e})")
                else:
                    f.write("License text not available")

                f.write("\n\n\n")

        print("NodeJS licenses successfully added to THIRD_PARTY_LICENSES.txt")
        return 0

    except Exception as e:
        print(f"Error combining licenses: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

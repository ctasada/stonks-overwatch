#!/usr/bin/env python3
"""
Generate THIRD_PARTY_LICENSES.txt file with all direct project dependencies.

This script extracts licenses for:
- Direct Python dependencies from pyproject.toml [project.dependencies]
- Optional Python dependencies from pyproject.toml [project.optional-dependencies]
- Production NodeJS dependencies from package.json

Transitive Python dependencies are excluded to keep the file size manageable.

Usage:
    poetry run python scripts/generate_licenses.py [--validate-only]

Options:
    --validate-only     Only validate existing licenses file without regenerating

How it works:
    1. Parse pyproject.toml to extract direct Python dependencies
    2. Generate Python licenses using pip-licenses tool
    3. Extract NodeJS production licenses using license-checker
    4. Combine both into THIRD_PARTY_LICENSES.txt
    5. Fix whitespace and formatting using pre-commit hooks
    6. Validate all direct dependencies are included

Configuration:
    See [tool.pip-licenses] section in pyproject.toml for pip-licenses configuration.
"""

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path


class LicenseGenerator:
    """Generate third-party licenses file."""

    def __init__(self):
        """Initialize the license generator."""
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.licenses_file = self.project_root / "THIRD_PARTY_LICENSES.txt"
        self.npm_licenses_file = self.project_root / "npm-licenses.json"

    def log(self, message: str, level: str = "INFO") -> None:
        """Print colored log message."""
        colors = {
            "INFO": "\033[34m",  # Blue
            "SUCCESS": "\033[32m",  # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",  # Red
            "RESET": "\033[0m",
        }
        color = colors.get(level, colors["INFO"])
        print(f"{color}{message}{colors['RESET']}")

    def normalize_package_name(self, dep: str) -> str:
        """
        Extract and normalize package name from dependency string.

        Args:
            dep: Dependency string (e.g., "django >= 6.0" or "ibind[oauth] >=0.1.21")

        Returns:
            Normalized package name (e.g., "django" or "ibind")
        """
        # Remove extras like [quotecast] or [oauth]
        dep = re.sub(r"\[.*?\]", "", dep)
        # Extract just the package name (before version constraints)
        name = re.split(r"[<>=!~]", dep)[0].strip()
        # Normalize to lowercase with underscores
        return name.lower().replace("-", "_")

    def get_direct_dependencies(self) -> list[str]:
        """
        Extract direct Python dependencies from pyproject.toml.

        Returns:
            List of package names (normalized, sorted)
        """
        with open(self.pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        # Get direct dependencies
        direct_deps = pyproject.get("project", {}).get("dependencies", [])

        # Get optional dependencies (e.g., briefcase group)
        optional_deps_groups = pyproject.get("project", {}).get("optional-dependencies", {})
        for _group_name, group_deps in optional_deps_groups.items():
            direct_deps.extend(group_deps)

        # Extract and normalize package names (remove duplicates)
        package_names = list({self.normalize_package_name(dep) for dep in direct_deps})
        package_names.sort()

        return package_names

    def generate_python_licenses(self, packages: list[str]) -> bool:
        """
        Generate Python licenses using pip-licenses.

        Args:
            packages: List of package names to include

        Returns:
            True if successful, False otherwise
        """
        try:
            self.log("Extracting Python dependencies...", "INFO")

            # Remove existing file
            if self.licenses_file.exists():
                self.licenses_file.unlink()

            # Run pip-licenses with the package list
            cmd = [
                "poetry",
                "run",
                "pip-licenses",
                "--packages",
                *packages,
                "--with-license-file",
                "--no-license-path",
            ]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                self.log(f"Error running pip-licenses: {result.stderr}", "ERROR")
                return False

            return True

        except Exception as e:
            self.log(f"Error generating Python licenses: {e}", "ERROR")
            return False

    def generate_nodejs_licenses(self) -> bool:
        """
        Generate NodeJS licenses using license-checker.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.log("Extracting NodeJS dependencies...", "INFO")

            # Run license-checker in src directory
            cmd = [
                "npx",
                "--yes",
                "license-checker",
                "--production",
                "--json",
                "--relativeLicensePath",
            ]

            result = subprocess.run(
                cmd,
                cwd=self.src_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                self.log(f"Error running license-checker: {result.stderr}", "ERROR")
                return False

            # Save to temporary JSON file
            self.npm_licenses_file.write_text(result.stdout)
            return True

        except Exception as e:
            self.log(f"Error generating NodeJS licenses: {e}", "ERROR")
            return False

    def combine_licenses(self) -> bool:
        """
        Combine NodeJS licenses with Python licenses.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.log("Combining licenses...", "INFO")

            # Read the NodeJS licenses JSON
            with open(self.npm_licenses_file) as f:
                data = json.load(f)

            # Append NodeJS licenses to the file
            with open(self.licenses_file, "a") as f:
                for pkg, info in sorted(data.items()):
                    # Parse package name and version
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
                        # Prepend 'src/' to the relative path
                        license_path = self.src_dir / license_file
                        try:
                            with open(license_path, encoding="utf-8", errors="ignore") as lf:
                                f.write(lf.read())
                        except Exception as e:
                            f.write(f"License text not available (Error: {e})")
                    else:
                        f.write("License text not available")

                    f.write("\n\n\n")

            # Clean up temporary file
            self.npm_licenses_file.unlink()
            return True

        except Exception as e:
            self.log(f"Error combining licenses: {e}", "ERROR")
            # Clean up temporary file on error
            if self.npm_licenses_file.exists():
                self.npm_licenses_file.unlink()
            return False

    def fix_formatting(self) -> bool:
        """
        Fix whitespace and formatting using pre-commit hooks.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.log("Fixing whitespace and end of file...", "INFO")

            # Run trailing-whitespace hook
            subprocess.run(
                ["poetry", "run", "pre-commit", "run", "trailing-whitespace", "--files", str(self.licenses_file)],
                cwd=self.project_root,
                check=False,
                capture_output=True,
            )

            # Run end-of-file-fixer hook
            subprocess.run(
                ["poetry", "run", "pre-commit", "run", "end-of-file-fixer", "--files", str(self.licenses_file)],
                cwd=self.project_root,
                check=False,
                capture_output=True,
            )

            return True

        except Exception as e:
            self.log(f"Error fixing formatting: {e}", "ERROR")
            return False

    def validate_licenses(self) -> bool:
        """
        Validate that all direct dependencies have licenses.

        Returns:
            True if all dependencies are included, False otherwise
        """
        try:
            # Get expected dependencies
            expected_deps = set(self.get_direct_dependencies())

            # Extract package names from licenses file
            licensed_packages = set()
            content = self.licenses_file.read_text()
            lines = content.split("\n")

            i = 0
            while i < len(lines):
                line = lines[i].strip()
                # Check if this looks like a package name
                if line and not line[0].isdigit() and len(line) > 0:
                    # Check if next line is a version number
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and (next_line[0].isdigit() or next_line == "UNKNOWN"):
                            licensed_packages.add(self.normalize_package_name(line))
                i += 1

            # Find missing packages
            missing = expected_deps - licensed_packages

            if missing:
                self.log(f"Missing {len(missing)} direct dependencies:", "ERROR")
                for pkg in sorted(missing):
                    self.log(f"  - {pkg}", "ERROR")
                return False

            self.log(f"✅ All {len(expected_deps)} direct Python dependencies have licenses!", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error validating licenses: {e}", "ERROR")
            return False

    def generate(self) -> bool:
        """
        Generate the complete licenses file.

        Returns:
            True if successful, False otherwise
        """
        self.log("Generating third-party licenses...", "INFO")

        # Get direct dependencies
        packages = self.get_direct_dependencies()
        self.log(f"Found {len(packages)} direct Python dependencies", "INFO")

        # Generate Python licenses
        if not self.generate_python_licenses(packages):
            return False

        # Generate NodeJS licenses
        if not self.generate_nodejs_licenses():
            return False

        # Combine licenses
        if not self.combine_licenses():
            return False

        # Fix formatting
        if not self.fix_formatting():
            return False

        # Validate
        if not self.validate_licenses():
            return False

        self.log(f"Third-party licenses saved to {self.licenses_file.name}", "SUCCESS")
        return True


def main() -> int:
    """Main entry point."""
    generator = LicenseGenerator()

    # Check for validate-only flag
    if len(sys.argv) > 1 and sys.argv[1] == "--validate-only":
        if not generator.licenses_file.exists():
            generator.log("THIRD_PARTY_LICENSES.txt not found!", "ERROR")
            return 1
        return 0 if generator.validate_licenses() else 1

    # Generate licenses
    return 0 if generator.generate() else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Convert CHANGELOG.md to AppStream releases XML format.

This script parses a CHANGELOG.md file following the Keep a Changelog format
and converts it to AppStream-compliant releases XML for metainfo.xml files.
"""

import os
import re
import sys
from typing import Dict, List, Optional


def parse_changelog(changelog_path: str) -> list:
    """Parse CHANGELOG.md and extract releases in AppStream format."""
    releases = []

    try:
        with open(changelog_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by version headers
        sections = re.split(r"^## \[", content, flags=re.MULTILINE)

        for section in sections:
            if not section.strip():
                continue

            # Extract version and date from first line
            lines = section.split("\n")
            first_line = lines[0] if lines else ""

            # Match version pattern: [version] or [version] - date
            match = re.match(r"^([^\]]+)\](?:\s*-\s*(\d{4}-\d{2}-\d{2}))?$", first_line)
            if not match:
                continue

            version = match.group(1).strip()
            date_str = match.group(2) if match.group(2) else None

            # Skip "Unreleased" for now (we'll handle current version separately)
            if version == "Unreleased":
                continue

            # Extract release notes (everything until next ## or end)
            release_content = "\n".join(lines[1:])
            # Remove separator lines and clean up
            release_content = re.sub(r"^---\s*$", "", release_content, flags=re.MULTILINE)
            release_content = release_content.strip()

            if release_content and date_str:
                releases.append(
                    {
                        "version": version,
                        "date": date_str,
                        "content": release_content,
                    }
                )
    except Exception as e:
        sys.stderr.write(f"Error parsing changelog: {e}\n")
        return []

    return releases


def convert_markdown_to_xml(text: str) -> str:
    """Convert markdown to AppStream XML format."""
    if not text:
        return ""

    lines = text.split("\n")
    xml_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Convert markdown bold **text** to <strong>text</strong>
        line = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", line)

        # Convert headers (### Header) to bold paragraphs
        if line.startswith("### "):
            header_text = line[4:].strip()
            xml_lines.append(f"        <p><strong>{header_text}</strong></p>")
        # Convert list items (4 spaces + dash or just dash)
        elif line.startswith("    - "):
            item_text = line[6:].strip()
            xml_lines.append(f"        <p>    • {item_text}</p>")
        elif line.startswith("- "):
            item_text = line[2:].strip()
            xml_lines.append(f"        <p>• {item_text}</p>")
        # Regular text
        else:
            xml_lines.append(f"        <p>{line}</p>")

    return "\n".join(xml_lines[:20])  # Limit to 20 lines


def _append_release_xml(xml_lines: List[str], version: str, date: str, content_md: str) -> None:
    """Append a release XML node with converted content to the xml_lines list."""
    xml_lines.append(f'    <release version="{version}" date="{date}">')
    xml_lines.append("      <description>")
    xml_lines.append(convert_markdown_to_xml(content_md))
    xml_lines.append("      </description>")
    xml_lines.append("    </release>")


def _find_current_release(releases: List[Dict[str, str]], current_version: str) -> Optional[Dict[str, str]]:
    """Find a release matching the current version or prefix."""
    for rel in releases:
        if rel["version"] == current_version or current_version.startswith(rel["version"]):
            return rel
    return None


def _get_unreleased_content(changelog_path: str) -> Optional[str]:
    """Extract the Unreleased section content from the changelog, if present."""
    try:
        with open(changelog_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Match content under the Unreleased header until the next header or end of file
        match = re.search(r"^## \[Unreleased\](?:\s*\n)?(.*?)(?=^## \[|\Z)", content, re.MULTILINE | re.DOTALL)
        if match:
            unreleased_content = match.group(1).strip()
            unreleased_content = re.sub(r"^---\s*$", "", unreleased_content, flags=re.MULTILINE)
            return unreleased_content if unreleased_content else None
    except Exception:
        return None
    return None


def generate_releases_xml(releases: list, current_version: str, current_date: str, changelog_path: str) -> str:
    """Generate AppStream releases XML."""
    xml_lines: List[str] = []

    # Add current version first (if it's a dev version, use Unreleased content)
    if current_version and current_date:
        current_release = _find_current_release(releases, current_version)

        if not current_release and "dev" in current_version:
            unreleased_content = _get_unreleased_content(changelog_path)
            if unreleased_content:
                _append_release_xml(xml_lines, current_version, current_date, unreleased_content)

        if current_release:
            _append_release_xml(
                xml_lines,
                current_release["version"],
                current_release["date"],
                current_release["content"],
            )
        elif not xml_lines:
            # Fallback: create a simple release entry
            xml_lines.append(f'    <release version="{current_version}" date="{current_date}">')
            xml_lines.append("      <description>")
            xml_lines.append(
                (
                    f"        <p>Version {current_version} release. See changelog at "
                    "https://github.com/ctasada/stonks-overwatch/blob/main/CHANGELOG.md "
                    "for details.</p>"
                )
            )
            xml_lines.append("      </description>")
            xml_lines.append("    </release>")

    # Add other recent releases (limit to last 5)
    count = 0
    for release in releases[:5]:
        # Skip if we already added this version
        if xml_lines and release["version"] in "\n".join(xml_lines):
            continue
        if count >= 4:  # Limit to 4 more releases (5 total)
            break

        _append_release_xml(xml_lines, release["version"], release["date"], release["content"])
        count += 1

    return "\n".join(xml_lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        sys.stderr.write("Usage: changelog-to-releases.py <changelog_path> <version> <date>\n")
        sys.exit(1)

    changelog_path = sys.argv[1]
    current_version = sys.argv[2]
    current_date = sys.argv[3]

    if not os.path.exists(changelog_path):
        sys.stderr.write(f"Error: Changelog file not found: {changelog_path}\n")
        sys.exit(1)

    releases = parse_changelog(changelog_path)
    releases_xml = generate_releases_xml(releases, current_version, current_date, changelog_path)

    if releases_xml:
        print(releases_xml)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

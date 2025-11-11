import os

from django.conf import settings
from django.contrib.staticfiles.finders import BaseFinder
from django.contrib.staticfiles.storage import StaticFilesStorage


class ExtraFilesFinder(BaseFinder):
    """
    Custom staticfiles finder to expose CHANGELOG.md, LICENSE, and THIRD_PARTY_LICENSES.txt
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = [
            os.path.join(settings.PROJECT_PATH, "CHANGELOG.md"),
            os.path.join(settings.PROJECT_PATH, "LICENSE"),
            os.path.join(settings.PROJECT_PATH, "THIRD_PARTY_LICENSES.txt"),
        ]
        self.storage = StaticFilesStorage(location=settings.PROJECT_PATH)

    def find(self, path, all=False):  # noqa: A002 - 'all' parameter required by Django's BaseFinder interface
        """
        Find static files matching the given path.

        Args:
            path: The path to search for
            all: If False, return first match. If True, return list of all matches.

        Returns:
            When all=False: A single file path (str) or None
            When all=True: A list of file paths (possibly empty)
        """
        matches = []
        for file_path in self.files:
            if os.path.basename(file_path) == path:
                if not all:
                    # Return first match immediately
                    return file_path
                matches.append(file_path)

        # Return None for single match mode, empty list for all matches mode
        return matches if all else None

    def list(self, ignore_patterns):
        for file_path in self.files:
            if os.path.exists(file_path):
                yield (os.path.basename(file_path), self.storage)

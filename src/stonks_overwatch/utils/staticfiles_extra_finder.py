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

    def find(self, path, all=False):
        for file_path in self.files:
            if os.path.basename(file_path) == path:
                return file_path if not all else [file_path]
        return [] if all else None

    def list(self, ignore_patterns):
        for file_path in self.files:
            if os.path.exists(file_path):
                yield (os.path.basename(file_path), self.storage)

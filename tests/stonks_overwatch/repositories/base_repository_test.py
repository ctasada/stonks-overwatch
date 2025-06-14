import json
import pathlib
from typing import Any, Dict, List, Optional, Type, TypeVar

from django.db import models

from django.test import TestCase

T = TypeVar("T", bound=models.Model)


class BaseRepositoryTest(TestCase):
    """Base class for repository tests that provides common functionality for loading and managing test data.

    This class handles:
    - Loading test data from JSON files
    - Creating model instances
    - Cleaning up test data
    - Common assertions for repository tests
    """

    model_class: Type[T]
    data_file: str

    def setUp(self):
        """Set up test data by loading it from the specified JSON file."""
        self.load_test_data()

    def load_test_data(self):
        """Load test data from the JSON file and create model instances.

        Override this method if you need custom data loading logic.
        """
        data_file = pathlib.Path(self.data_file)

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects: Dict[str, T] = {}
        for key, value in data.items():
            obj = self.model_class.objects.create(**value)
            self.created_objects[key] = obj

    def tearDown(self):
        """Clean up created test objects."""
        for obj in self.created_objects.values():
            obj.delete()

    def get_test_object(self, key: str) -> Optional[T]:
        """Get a test object by its key."""
        return self.created_objects.get(key)

    def assert_object_exists(self, key: str) -> None:
        """Assert that a test object exists."""
        self.assertIn(key, self.created_objects)

    def assert_object_attributes(self, key: str, **attributes) -> None:
        """Assert that a test object has the specified attributes."""
        obj = self.get_test_object(key)
        self.assertIsNotNone(obj)
        for attr_name, expected_value in attributes.items():
            self.assertEqual(getattr(obj, attr_name), expected_value)

    def assert_list_length(self, items: List[Any], expected_length: int) -> None:
        """Assert that a list has the expected length."""
        self.assertEqual(len(items), expected_length)

    def assert_dict_contains(self, data: Dict[str, Any], **expected_items) -> None:
        """Assert that a dictionary contains the expected key-value pairs."""
        for key, expected_value in expected_items.items():
            self.assertIn(key, data)
            self.assertEqual(data[key], expected_value)

    def assert_date_equals(self, actual_date: str, expected_date: str) -> None:
        """Assert that two date strings are equal."""
        self.assertEqual(actual_date, expected_date)

    def assert_decimal_equals(self, actual: float, expected: float, places: int = 6) -> None:
        """Assert that two decimal numbers are equal up to the specified number of decimal places."""
        self.assertAlmostEqual(actual, expected, places=places)

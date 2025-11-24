import os
import zipfile

from django.apps import apps
from django.core import serializers
from django.db import connections, router
from django.db.backends.utils import CursorWrapper


def dictfetchall(cursor: CursorWrapper) -> list[dict]:
    """Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [snake_to_camel(col[0]) for col in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def dictfetchone(cursor: CursorWrapper) -> dict | None:
    """Returns the first row from a cursor as a dict.
    Assume the column names are unique.
    """
    results = dictfetchall(cursor)
    if not results:
        return None
    return results[0]


def get_connection_for_model(model_class):
    """
    Get the appropriate database connection for a model based on the database router.

    This function ensures that database operations respect the DEMO_MODE environment
    variable and use the correct database (default or demo).

    Args:
        model_class: The Django model class to get the connection for

    Returns:
        Database connection object that respects the router configuration
    """
    db_alias = router.db_for_read(model_class)
    return connections[db_alias]


def snake_to_camel(snake_str):
    """Converts snake_case to camelCase"""
    components = snake_str.split("_")
    # Capitalize the first letter of each word except the first word
    return components[0] + "".join(x.title() for x in components[1:])


def get_models():
    """Get the necessary models for the database dump"""

    models = []
    for model in apps.get_models():
        app_label = model._meta.app_label

        if app_label in ["stonks_overwatch"]:
            models.append(model)

    return models


def dump_database(output_file="db_dump.zip", database="default"):
    """Dump database content to JSON file"""

    if database == "demo":
        os.environ["DEMO_MODE"] = "True"

    print(f"Dumping database to {output_file}...")

    # Get all objects from selected models
    objects_to_serialize = []
    for model in get_models():
        objects = model.objects.all()
        objects_to_serialize.extend(objects)
        print(f"Found {objects.count()} objects in {model._meta.app_label}.{model._meta.model_name}")

    # Serialize to JSON
    serialized_data = serializers.serialize("json", objects_to_serialize, indent=2)

    # Write to a file
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("db_dump.json", serialized_data)

    print(f"Successfully dumped {len(objects_to_serialize)} objects to {output_file}")

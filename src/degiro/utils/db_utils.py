import re

from django.db.backends.utils import CursorWrapper


def dictfetchall(cursor: CursorWrapper) -> dict:
    """Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def dictfetchone(cursor: CursorWrapper) -> dict:
    """Returns the first row from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    result = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return result[0]

def camel_to_snake_case(camel_str):
    # Insert an underscore before each uppercase letter
    snake_str = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    # Handle cases where there are multiple uppercase letters together (e.g., HTTPResponse)
    snake_str = re.sub("([a-z0-9])([A-Z])", r"\1_\2", snake_str)
    # Convert the entire string to lowercase
    return snake_str.lower()

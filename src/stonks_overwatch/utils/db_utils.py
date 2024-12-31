from django.db.backends.utils import CursorWrapper


def dictfetchall(cursor: CursorWrapper) -> list[dict]:
    """Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [snake_to_camel(col[0]) for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def dictfetchone(cursor: CursorWrapper) -> dict:
    """Returns the first row from a cursor as a dict.
    Assume the column names are unique.
    """
    return dictfetchall(cursor)[0]

def snake_to_camel(snake_str):
    """Converts snake_case to camelCase"""
    components = snake_str.split("_")
    # Capitalize the first letter of each word except the first word
    return components[0] + "".join(x.title() for x in components[1:])

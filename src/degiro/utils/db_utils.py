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

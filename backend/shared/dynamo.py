import boto3

from shared.constants import TABLE_NAME

_table = None


def get_table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(TABLE_NAME)
    return _table


def reset_table():
    """Reset cached table reference. Used in tests."""
    global _table
    _table = None

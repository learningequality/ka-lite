from contextlib import contextmanager

from django.db import transaction


@contextmanager
def inside_transaction():
    '''Perform the database operations inside a transaction.  This is a
    basic reimplementation of django.db.transactions.atomic, which isn't
    present in django 1.5.
    '''
    savepoint = transaction.savepoint()
    try:
        yield
    except Exception:
        transaction.savepoint_rollback(savepoint)
        raise
    else:
        transaction.savepoint_commit(savepoint)

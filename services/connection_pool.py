"""Compatibility adapter for existing conn.close() callers."""
from threading import Lock

_pool = None
_lock = Lock()


class BorrowedConnection:
    def __init__(self, pool):
        self._pool = pool
        self._connection = pool.getconn(timeout=10)
        self._returned = False

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def close(self):
        if not self._returned:
            self._returned = True
            self._pool.putconn(self._connection)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                self._connection.rollback()
            else:
                self._connection.commit()
        finally:
            self.close()


def borrow_connection(url, row_factory):
    global _pool
    from psycopg_pool import ConnectionPool
    with _lock:
        if _pool is None:
            _pool = ConnectionPool(url, min_size=0, max_size=6, max_waiting=12, timeout=10,
                                   check=ConnectionPool.check_connection,
                                   kwargs={'row_factory': row_factory, 'connect_timeout': 10, 'prepare_threshold': None})
    return BorrowedConnection(_pool)

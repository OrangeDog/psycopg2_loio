"""
Wrapping an lobject (PostgreSQL Large Object) with a file-like interface.

Provides efficient read/write streaming and seeking.

.. note::
    The provided lobject must be open and in binary mode.

Example
--------
.. code:: python

    with psycopg2.connect() as conn:
        with psycopg2_loio.as_binary(conn.lobject(1234, mode='wb') as lo:
            with open('file.bin', 'rb') as file:
                shutil.copyfileobj(file, lo)
        conn.commit()

        with psycopg2_loio.as_text(conn.lobject(4567, mode='rb'),
                                   encoding='ascii',
                                   errors='replace') as lo:
            for line in lo:
                print(line.strip()))

"""

import errno
import io
import os

from typing import Optional, TextIO, BinaryIO

import psycopg2

__all__ = ['LargeObjectIO', 'as_binary', 'as_text']


class LargeObjectIO(io.BufferedIOBase, io.RawIOBase):
    """Adapt a PostgreSQL Large Object to a File-like object."""

    max_read_size = io.DEFAULT_BUFFER_SIZE

    def __init__(self, lo: psycopg2.extensions.lobject):
        """
        Create a new raw wrapper around the lobject.

        :param lo: lobject to wrap
        """
        if 'b' not in lo.mode:
            raise ValueError('lobject must be open in binary mode')
        self.lo = lo

    def close(self):
        self.lo.close()

    @property
    def closed(self):
        return self.lo.closed

    def readable(self):
        return not self.lo.closed and 'r' in self.lo.mode

    def read(self, size: Optional[int] = -1) -> bytes:
        if size is None or size < 0 or size > self.max_read_size:
            size = self.max_read_size
        return self.lo.read(size)

    def seekable(self):
        return not self.lo.closed

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        return self.lo.seek(offset, whence)

    def tell(self) -> int:
        return self.lo.tell()

    def truncate(self, size: Optional[int] = None) -> int:
        return self.lo.truncate(size)

    def writable(self):
        return not self.lo.closed and 'w' in self.lo.mode

    def write(self, data) -> int:
        return self.lo.write(data)


def as_binary(lo: psycopg2.extensions.lobject) -> BinaryIO:
    """
    Wrap an lobject as a BinaryIO.

    :param lo: lobject to wrap
    """
    raw = LargeObjectIO(lo)
    if raw.readable() and raw.writable():
        return io.BufferedRandom(raw)
    elif raw.readable():
        return io.BufferedReader(raw)
    elif raw.writable():
        return io.BufferedWriter(raw)
    else:
        raise OSError(errno.EIO, "closed")


def as_text(lo: psycopg2.extensions.lobject, **kwargs) -> TextIO:
    """
    Wrap an lobject as a BinaryIO.

    :param lo: lobject to wrap
    :param kwargs: additional arguments as per io.TextIOWrapper
    """
    return io.TextIOWrapper(as_binary(lo), **kwargs)

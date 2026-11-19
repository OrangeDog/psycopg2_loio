# psycopg2_loio

Wrap an `lobject` (PostgreSQL Large Object) with a file-like interface.

Installation
------------
```sh
pip install psycopg2-loio
```

Usage
-----
```python
import shutil

import psycopg2
import psycopg2_loio

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
```

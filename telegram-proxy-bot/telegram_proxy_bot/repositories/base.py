from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from ..db import db


@contextmanager
def db_context() -> Iterator:
    with db() as conn:
        yield conn

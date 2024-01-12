"""
byceps.util.iterables
~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from collections.abc import Callable, Iterable, Iterator
from itertools import tee
from typing import TypeVar


T = TypeVar('T')

Predicate = Callable[[T], bool]


def find(iterable: Iterable[T], predicate: Predicate) -> T | None:
    """Return the first element in the iterable that matches the
    predicate.

    If none does, return ``None``.
    """
    for elem in iterable:
        if predicate(elem):
            return elem

    return None


def index_of(iterable: Iterable[T], predicate: Predicate) -> int | None:
    """Return the (0-based) index of the first element in the iterable
    that matches the predicate.

    If none does, return ``None``.
    """
    for i, elem in enumerate(iterable):
        if predicate(elem):
            return i

    return None


def pairwise(iterable: Iterable[T]) -> Iterator[tuple[T, T]]:
    """Return each element paired with its next one.

    Example:
        xs -> (x0, x1), (x1, x2), (x2, x3), ...

    As seen in the Python standard library documentation of the
    `itertools` module:
    https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b, strict=False)


def partition(
    iterable: Iterable[T], predicate: Predicate
) -> tuple[list[T], list[T]]:
    """Partition the iterable into two lists according to the predicate.

    The first list contains all elements that satisfy the predicate, the
    second list contains all elements that do not.

    Relative element order is preserved.
    """
    satisfied, unsatisfied = [], []

    for elem in iterable:
        if predicate(elem):
            satisfied.append(elem)
        else:
            unsatisfied.append(elem)

    return satisfied, unsatisfied

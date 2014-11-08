QueryStream
===========

An offline, mostly lazy reimplementation of Django's QuerySet.
Provides QuerySet-like semantics for any iterator.  Useful for 
converting existing code relying on ORM queries for offline
operation.

::

    >>> from collections import namedtuple
    >>> from querystream import QueryStream
    >>> T = namedtuple('T', ['foo', 'bar'])
    >>> tuples = [T('a', 1), T('a', 2), T('b', 1), T('b', 2)]
    >>> qs = QueryStream(tuples)
    >>> list(qs.filter(bar=1))
    [T(foo='a', bar=1), T(foo='b', bar=1)]
    >>> qs.filter(foo='b', bar=1).first()
    T(foo='b', bar=1)


Installation
============

::

    pip install querystream


Running tests
=============

::

    pip install pytest model-mommy
    py.test


Changes
=======

1.0.0
-----

* First published API

from itertools import chain, ifilter, islice
from functools import partial
from operator import and_


class QueryStream(object):
    def __init__(self, iterable):
        self.iterable = iterable

    def all(self):
        """
        Creates a concrete intermediate representation of
        the query stream.  Equal to `qs2 = QueryStream(list(qs1))`.
        """
        return QueryStream(list(self.iterable))

    def filter(self, *qs, **kwargs):
        """
        Returns a new QueryStream with only objects that match
        provided predicates (that can be Q objects or keyword
        arguments matching the Q constructor semantics):

            qs.filter(Q(a=val) | Q(b=val), c=val)

        """
        composite_q = reduce(and_, qs, Q(**kwargs))
        return QueryStream(ifilter(composite_q.fun, self.iterable))

    def exclude(self, *qs, **kwargs):
        """
        Like filter, but rejects objects matching predicates.
        """
        composite_q = ~reduce(and_, qs, Q(**kwargs))
        return QueryStream(ifilter(composite_q.fun, self.iterable))

    def order_by(self, selector):
        if selector.startswith('-'):
            key_fun = lambda obj: -_select_attr(obj, selector[1:])
        else:
            key_fun = lambda obj: _select_attr(obj, selector)
        return QueryStream(sorted(self.iterable, key=key_fun))

    def __iter__(self):
        return iter(self.iterable)

    def __getslice__(self, i, j):
        return QueryStream(islice(self.iterable, i, j))

    def __or__(self, other):
        return QueryStream(chain(self.iterable, other.iterable))

    @staticmethod
    def none():
        return QueryStream(())


class Q(object):
    """
    A callable object that returns the value of predicate 
    for a given object:

        q1 = Q(attribute1=value, attribute2=value)
        q2 = Q(lambda x: x.attribute1 < value)
        q1(object) == True

    Q supports Django-style related object attributes:

        Q(related_object__attribute=value)

    Q objects support the following logical operators: `&`, `|`, `~`.
    """
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            self.fun = args[0]
        else:
            self.fun = partial(self._match, kwargs.items())

    @staticmethod
    def _match(kvs, obj):
        return all(_select_attr(obj, k) == v for k, v in kvs)

    def __call__(self, obj):
        return self.fun(obj)

    def __and__(self, other):
        return Q(lambda obj: self.fun(obj) and other.fun(obj))

    def __or__(self, other):
        return Q(lambda obj: self.fun(obj) or other.fun(obj))

    def __invert__(self):
        return Q(lambda obj: not self.fun(obj))


def _select_attr(obj, selector):
    """
    Gets an attribute for selector, e.g.

        _select_attr(o, 'x__y__z')

    evaluates as

        o.x.y.z

    """
    split_selector = selector.split('__')
    return reduce(getattr, split_selector, obj)


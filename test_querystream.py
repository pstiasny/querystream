from django.conf import settings
settings.configure()

# required since Django 1.7
try:
    from django import setup as django_setup
except ImportError:
    pass
else:
    django_setup()

from itertools import cycle
import pytest
from model_mommy import mommy

from django.db import models
from django.forms.models import model_to_dict
from querystream import Q, QueryStream


class RelatedModel(models.Model):
    class Meta:
        app_label = 'testapp'
    other_number = models.IntegerField()


class MainModel(models.Model):
    class Meta:
        app_label = 'testapp'
    name = models.CharField(max_length=30)
    creation = models.DateTimeField()
    number = models.IntegerField()
    related_model = models.ForeignKey(RelatedModel)


def test_iterable():
    objs = mommy.prepare(MainModel, _quantity=3)
    qs = QueryStream(objs)
    assert list(qs.iterable) == objs


def test_q():
    q = Q(number=123)
    good = mommy.prepare(MainModel, number=123)
    bad = mommy.prepare(MainModel, number=122)
    assert q(good)
    assert not q(bad)


def test_functional_q():
    q = Q(lambda obj: obj.number == 123)
    good = mommy.prepare(MainModel, number=123)
    bad = mommy.prepare(MainModel, number=122)
    assert q(good)
    assert not q(bad)


def test_composited_q():
    q1 = Q(number=123)
    q2 = Q(name="test")
    matches_q1 = mommy.prepare(MainModel, number=123)
    matches_q2 = mommy.prepare(MainModel, name="test")
    matches_both = mommy.prepare(MainModel, number=123, name="test")
    all_objs = (matches_q1, matches_q2, matches_both)

    assert [q1(x) | q2(x) for x in all_objs] == [True, True, True]
    assert [q1(x) & q2(x) for x in all_objs] == [False, False, True]


def test_negated_q():
    q = ~Q(number=123)
    good = mommy.prepare(MainModel, number=123)
    bad = mommy.prepare(MainModel, number=122)
    assert not q(good)
    assert q(bad)


def test_relation_attribute_q():
    good_related = mommy.prepare(RelatedModel, other_number=123)
    good = mommy.prepare(MainModel, related_model=good_related)
    bad_related = mommy.prepare(RelatedModel, other_number=0)
    bad = mommy.prepare(MainModel, related_model=bad_related)
    q = Q(related_model__other_number=123)
    assert q(good)
    assert not q(bad)


def test_simple_filter():
    good = mommy.prepare(MainModel, number=123)
    bad = mommy.prepare(MainModel, number=122)
    qs = QueryStream((good, bad))
    filtered_qs = qs.filter(number=123)
    assert list(filtered_qs.iterable) == [good]


def test_multi_filter():
    matches_first = mommy.prepare(MainModel, number=123)
    matches_second = mommy.prepare(MainModel, name="test")
    matches_both = mommy.prepare(MainModel, number=123, name="test")
    all_objs = (matches_first, matches_second, matches_both)

    qs = QueryStream(all_objs)
    filtered_qs = qs.filter(number=123, name="test")
    assert list(filtered_qs.iterable) == [matches_both]


def test_q_filter():
    matches_first = mommy.prepare(MainModel, number=123)
    matches_second = mommy.prepare(MainModel, name="test")
    matches_none = mommy.prepare(MainModel, number=122, name="no")
    all_objs = (matches_first, matches_second, matches_none)

    qs = QueryStream(all_objs)
    filtered_qs = qs.filter(~Q(number=123), ~Q(name="test"))
    assert list(filtered_qs.iterable) == [matches_none]


def test_exclude():
    good = mommy.prepare(MainModel, number=123)
    bad = mommy.prepare(MainModel, number=122)
    qs = QueryStream((good, bad))
    filtered_qs = qs.exclude(number=123)
    assert list(filtered_qs.iterable) == [bad]


def test_none():
    assert QueryStream.none().iterable is ()
    assert QueryStream(('test',)).none().iterable is ()


def test_iter():
    qs = QueryStream(('a', 'b'))
    out = []
    for obj in qs:
        out.append(obj)
    assert out == ['a', 'b']


def test_slice():
    qs = QueryStream('abcd')
    assert list(qs[:2]) == ['a', 'b']
    assert list(qs[2:]) == ['c', 'd']
    assert list(qs[1:3]) == ['b', 'c']

    # test over an infinite sequence
    qs = QueryStream(cycle('abcd'))[:6]
    assert list(qs) == ['a', 'b', 'c', 'd', 'a', 'b']


def test_pipe_chain():
    qs1 = QueryStream('ab')
    qs2 = QueryStream('c')
    qs3 = QueryStream('d')
    assert list(qs1 | qs2 | qs3) == ['a', 'b', 'c', 'd']


def test_shared_source():
    # if the source is concrete, a new iterator will be created for each
    # final QueryStream
    src = 'abcde'
    qs = QueryStream(src)
    qs1 = qs.filter(Q(lambda c: c != 'b'))
    qs2 = qs.filter(Q(lambda c: c != 'a'))
    assert list(qs1) == ['a', 'c', 'd', 'e']
    assert list(qs2) == ['b', 'c', 'd', 'e']

    # if the source is an iterator, it will be shared among all final
    # QuerySreams
    src = iter('abcde')
    qs = QueryStream(src)
    qs1 = qs.filter(Q(lambda c: c != 'b'))
    qs2 = qs.filter(Q(lambda c: c != 'a'))
    assert list(qs1) == ['a', 'c', 'd', 'e']
    assert list(qs2) == []  # depleted by qs1


def test_all():
    src = iter('abcde')
    qs = QueryStream(src).all()
    qs1 = qs.filter(Q(lambda c: c != 'b'))
    qs2 = qs.filter(Q(lambda c: c != 'a'))
    assert list(qs1) == ['a', 'c', 'd', 'e']
    assert list(qs2) == ['b', 'c', 'd', 'e']


def test_order_by():
    o1 = mommy.prepare(MainModel, name='a')
    o2 = mommy.prepare(MainModel, name='b')
    o3 = mommy.prepare(MainModel, name='c')
    qs = QueryStream((o2, o1, o3))

    assert list(qs.order_by('name')) == [o1, o2, o3]
    assert list(qs.order_by('-name')) == [o3, o2, o1]


def test_first():
    assert QueryStream((1, 2, 3)).first() == 1
    assert QueryStream.none().first() is None


def test_repr():
    qs = QueryStream([1, 2, 3])

    assert repr(qs) == 'QueryStream([1, 2, 3])'
    assert str(qs) == 'QueryStream([1, 2, 3])'
    assert unicode(qs) == 'QueryStream([1, 2, 3])'

    assert repr(qs.filter(Q(lambda x: x > 2)).all()) == 'QueryStream([3])'

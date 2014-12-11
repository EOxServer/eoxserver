# By Christian Muirhead, Menno Smits and Michael Foord 2008
# WTF license
# http://voidspace.org.uk/blog

"""
``total_ordering`` and ``force_total_ordering`` are class decorators for
Python 2.6 & Python 3.

They provides *all* the rich comparison methods on a class by defining *any*
one of '__lt__', '__gt__', '__le__', '__ge__'.

``total_ordering`` fills in all unimplemented rich comparison methods, assuming
at least one is implemented. ``__lt__`` is taken as the base comparison method
on which the others are built, but if that is not available it will be
constructed from the first one found.

``force_total_ordering`` does the same, but having taken a comparison method as
the base it fills in *all* the others - this overwrites additional comparison
methods that may be implemented, guaranteeing consistent comparison semantics.

::

    from total_ordering import total_ordering

    @total_ordering
    class Something(object):
        def __init__(self, value):
            self.value = value
        def __lt__(self, other):
            return self.value < other.value

It also works with Python 2.5, but you need to do the wrapping yourself:

::

    from total_ordering import total_ordering

    class Something(object):
        def __init__(self, value):
            self.value = value
        def __lt__(self, other):
            return self.value < other.value

    total_ordering(Something)

It would be easy to modify for it to work as a class decorator for Python
3.X and a metaclass for Python 2.X.
"""

import sys as _sys

if _sys.version_info[0] == 3:
    def _has_method(cls, name):
        for B in cls.__mro__:
            if B is object:
                continue
            if name in B.__dict__:
                return True
        return False
else:
    def _has_method(cls, name):
        for B in cls.mro():
            if B is object:
                continue
            if name in B.__dict__:
                return True
        return False


def _ordering(cls, overwrite):
    def setter(name, value):
        if overwrite or not _has_method(cls, name):
            value.__name__ = name
            setattr(cls, name, value)

    comparison = None
    if not _has_method(cls, '__lt__'):
        for name in 'gt le ge'.split():
            if not _has_method(cls, '__' + name + '__'):
                continue
            comparison = getattr(cls, '__' + name + '__')
            if name.endswith('e'):
                eq = lambda s, o: comparison(s, o) and comparison(o, s)
            else:
                eq = lambda s, o: not comparison(s, o) and not comparison(o, s)
            ne = lambda s, o: not eq(s, o)
            if name.startswith('l'):
                setter('__lt__', lambda s, o: comparison(s, o) and ne(s, o))
            else:
                setter('__lt__', lambda s, o: comparison(o, s) and ne(s, o))
            break
        assert comparison is not None, (
            'must have at least one of ge, gt, le, lt'
        )

    setter('__ne__', lambda s, o: s < o or o < s)
    setter('__eq__', lambda s, o: not s != o)
    setter('__gt__', lambda s, o: o < s)
    setter('__ge__', lambda s, o: not (s < o))
    setter('__le__', lambda s, o: not (s > o))
    return cls


def total_ordering(cls):
    return _ordering(cls, False)


def force_total_ordering(cls):
    return _ordering(cls, True)

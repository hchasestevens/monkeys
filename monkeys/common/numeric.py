"""Common numeric functions."""

import functools
from numbers import Real

from monkeys.typing import params, rtype, ignore


@params(Real, Real)
@rtype(Real)
def add(x, y):
    return x + y


@params(Real, Real)
@rtype(Real)
def sub(x, y):
    return x - y


@params(Real, Real)
@rtype(Real)
@ignore(float('NaN'), ZeroDivisionError)
def mod(x, y):
    return x % y


@params(Real, Real)
@rtype(Real)
def mul(x, y):
    return x * y


@params(Real, Real)
@rtype(Real)
@ignore(float('NaN'), ZeroDivisionError)
def div(x, y):
    return x / y


@params(Real, Real)
@rtype(Real)
@ignore(float('NaN'), ZeroDivisionError)
def exp(x, y):
    return x ** y


@params(Real)
@rtype([Real])
@ignore([], Exception)
def num_range(x):
    return list(range(int(x)))

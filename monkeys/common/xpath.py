"""Common functions for XPath expression generation."""

from monkeys.typing import params, rtype, constant, free


class NodeName(object):
    """Specifies an available node name."""

    def __init__(self, node_name):
        constant(NodeName, node_name)


NodeName('*')


class Expression(object):
    """Represents an XPath expression."""

    def __init__(self, expression):
        constant(Expression, expression)


@params(NodeName)
@rtype(Expression)
def global_node(node_name):
    return './/{}'.format(node_name)


@params(NodeName)
@rtype(Expression)
def local_node(node_name):
    return './{}'.format(node_name)


@params(Expression, NodeName)
@rtype(Expression)
def children(expr, node_name):
    return '{}/{}'.format(expr, node_name)


@params(Expression, NodeName)
@rtype(Expression)
def descendants(expr, node_name):
    return '{}//{}'.format(expr, node_name)


class Axis(object):
    """One of the XPath standard axes."""

    def __init__(self, axis_name):
        constant(Axis, axis_name)


axes = (
    'ancestor',
    'ancestor-or-self',
    'child',
    'descendant',
    'descendant-or-self',
    'following',
    'following-sibling',
    'parent',
    'preceding',
    'preceding-sibling',
    'self',
)

for axis_name in axes:
    Axis(axis_name)


@params(Expression, Axis, NodeName)
@rtype(Expression)
def child_axis(expr, axis, node_name):
    return '{}/{}::{}'.format(expr, axis, node_name)


class Condition(object):
    """A conditional predicate, applicable to an expression."""
    pass


@params(Axis, NodeName)
@rtype(Condition)
def specific_node(axis, node_name):
    return '{}::{}'.format(axis, node_name)


@params(Condition, Condition)
@rtype(Condition)
def cond_and(c1, c2):
    return '{} and {}'.format(c1, c2)


@params(Condition, Condition)
@rtype(Condition)
def cond_or(c1, c2):
    return '{} or {}'.format(c1, c2)


@params(Condition)
@rtype(Condition)
def cond_not(c):
    return 'not({})'.format(c)


class ConditionedExpression(object):
    """We introduce this to prevent stacking of multiple conditional clauses."""
    pass


@params(Expression, Condition)
@rtype(ConditionedExpression)
def apply_cond(expr, cond):
    return '{}[{}]'.format(expr, cond)


@params(ConditionedExpression, NodeName)
@rtype(Expression)
def condexpr_child(cond_expr, node_name):
    return '{}/{}'.format(cond_expr, node_name)


@params(ConditionedExpression, NodeName)
@rtype(Expression)
def condexpr_descendant(cond_expr, node_name):
    return '{}//{}'.format(cond_expr, node_name)


class Number(object):
    """A number."""

    def __init__(self, n):
        constant(Number, str(n))


Number(1)
Number(0)


class Measurement(object):
    """
    A number taken from a real-world value, introduced
    to avoid tautological conditions.
    """
    pass

free(Number, Measurement)


@params(Expression)
@rtype(Measurement)
def count(elem):
    return 'count({})'.format(elem)


@params(Measurement, Number)
@rtype(Condition)
def greater_than(num1, num2):
    return '{} > {}'.format(num1, num2)


@params(Measurement, Number)
@rtype(Condition)
def num_eq(num1, num2):
    return '{} = {}'.format(num1, num2)


class AttributeName(object):
    """Name of an accessible attribute."""

    def __init__(self, attr_name):
        constant(AttributeName, attr_name)


AttributeName('id')


@params(AttributeName)
@rtype(Condition)
def attribute_exists(attr_name):
    return '@{}'.format(attr_name)


class AttributeValue(object):
    """Potential value of an attribute."""
    
    def __init__(self, attr_value):
        constant(AttributeValue, attr_value)
        
        
AttributeValue('')


@params(AttributeName, AttributeValue)
@rtype(Condition)
def attribute_equals(attr_name, attr_value):
    return "@{} = '{}'".format(attr_name, attr_value)

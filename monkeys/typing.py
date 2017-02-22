import functools
import collections

from past.builtins import basestring


REGISTERED_TYPES = set()
_STRING_TYPE_MAPPINGS = {}


_func = collections.namedtuple('Function', 'params rtype')
def func(*args):
    """Function container for higher-order parameters and return types."""
    assert len(args) >= 2
    return _func(tuple(args[:-1]), args[-1])


def __id(x):
    """Identity function."""
    return x


def convert_type(t):
    """Map given type into representation suitable for internal usage."""
    if not t:
        converted = None
    elif isinstance(t, collections.Mapping):
        converted = (collections.Mapping, convert_type(next(t.iterkeys())), convert_type(next(t.itervalues())))
    elif isinstance(t, _func):
        converted = (_func, tuple(map(convert_type, t.params)), convert_type(t.rtype))
    elif isinstance(t, basestring):
        try:
            converted = _STRING_TYPE_MAPPINGS[t]
        except KeyError:
            converted = type(t, (object,), {})
            _STRING_TYPE_MAPPINGS[t] = converted
    elif isinstance(t, collections.Iterable):
        converted = (collections.Iterable, convert_type(t[0]))
    else:
        converted = t
    REGISTERED_TYPES.add(converted)
    return converted


def prettify_converted_type(t):
    """Return human-readable representation of internal type."""
    if t is None:
        return 'None'
    if isinstance(t, type):
        return t.__name__
    try:
        __, listed_t = t
        return '[{}]'.format(prettify_converted_type(listed_t))
    except (ValueError, TypeError):
        pass
    try:
        outer, first_inner, second_inner = t
        formatted_inners = map(prettify_converted_type, (first_inner, second_inner))
        if outer is collections.Mapping:
            return '{{{}: {}}}'.format(*formatted_inners)
        if outer is _func:
            return '{} -> {}'.format(*formatted_inners)
    except (ValueError, TypeError):
        pass
    return str(t)


def __type_annotations_factory():
    """Create rtype, params, constant, and lookup_rtype functions."""
    RTYPES = collections.defaultdict(list)

    def register_first_class_function(f):
        """
        Register lifted version of function for use with higher-order 
        functions.
        """
        @params(convert=False, first_class=False)
        @rtype((_func, f.__params, f.rtype), convert=False, first_class=False)
        def const_f():
            return f
        const_f.__name__ = '_FC_{}'.format(f.__name__)

    def check_for_registration(f):
        """
        Determine if a function has had both return type and parameter 
        types specified, registering it as a first-class function if 
        so.
        """
        if hasattr(f, 'rtype') and hasattr(f, '__params'):
            register_first_class_function(f)
            return True

    def allowed_children_factory(param_types):
        """
        Return a list of the appropriately-typed constants and functions 
        conforming to each of the specified parameter types.
        """
        return lambda: [RTYPES[param_type] for param_type in param_types]

    def rtype(return_type, convert=True, first_class=True):
        """Specify the return type of a function."""
        _convert_type = convert_type if convert else __id
        check = check_for_registration if first_class else __id
        def decorator(f):
            _return_type = _convert_type(return_type)
            RTYPES[_return_type].append(f)
            f.readable_rtype = prettify_converted_type(_return_type)
            f.rtype = _return_type
            check(f)
            return f
        return decorator

    def params(*param_types, **kwargs):
        """Specify the required types for a function."""
        _convert_type = convert_type if kwargs.get('convert', True) else __id
        check = check_for_registration if kwargs.get('first_class', True) else __id
        def decorator(f):
            _param_types = tuple(map(_convert_type, param_types))
            f.allowed_children = allowed_children_factory(_param_types)
            f.readable_param_list = map(prettify_converted_type, _param_types)
            f.readable_params = ', '.join(f.readable_param_list)
            f.__params = _param_types
            check(f)
            return f
        return decorator

    def constant(return_type, value):
        """Register a constant value under the given type."""
        @params()
        @rtype(return_type)
        def _const():
            return value
        _const.__name__ += '_' + str(value)
        return value

    def lookup_rtype(return_type, convert=True):
        """Find functions and constants of the given return type."""
        return RTYPES[(convert_type if convert else __id)(return_type)]
    
    def deregister(fn):
        """Remove function from usage."""
        for fn_list in RTYPES.values():
            try:
                fn_list.remove(fn)
            except ValueError:
                continue

    return rtype, params, constant, lookup_rtype, deregister


rtype, params, constant, lookup_rtype, deregister = __type_annotations_factory()


def ignore(failure_value, *exceptions):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except exceptions:
                return failure_value
        return wrapper
    return decorator

import collections


REGISTERED_TYPES = set()
_func = collections.namedtuple('Function', 'params rtype')
def func(*args):
    assert len(args) >= 2
    return _func(tuple(args[:-1]), args[-1])


def __id(x):
    return x


def convert_type(t):
    if not t:
        converted = None
    elif isinstance(t, collections.Mapping):
        converted = (collections.Mapping, convert_type(next(t.iterkeys())), convert_type(next(t.itervalues())))
    elif isinstance(t, _func):
        converted = (_func, tuple(map(convert_type, t.params)), convert_type(t.rtype))
    elif isinstance(t, collections.Iterable):
        converted = (collections.Iterable, convert_type(t[0]))
    else:
        converted = t
    REGISTERED_TYPES.add(converted)
    return converted


def prettify_converted_type(t):
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
        if outer == _func:
            return '{} -> {}'.format(*formatted_inners)
    except (ValueError, TypeError):
        pass
    return str(t)


def __type_annotations_factory():
    RTYPES = collections.defaultdict(list)

    def register_first_class_function(f):
        @params(convert=False, first_class=False)
        @rtype((_func, f.__params, f.rtype), convert=False, first_class=False)
        def const_f():
            return f
        const_f.func_name = '_FC_{}'.format(f.func_name)

    def check_for_registration(f):
        if hasattr(f, 'rtype') and hasattr(f, '__params'):
            register_first_class_function(f)

    def allowed_children_factory(param_types):
        return lambda: [RTYPES[param_type] for param_type in param_types]

    def rtype(return_type, convert=True, first_class=True):
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
        _convert_type = convert_type if kwargs.get('convert', True) else __id
        check = check_for_registration if kwargs.get('first_class', True) else __id
        def decorator(f):
            _param_types = tuple(map(_convert_type, param_types))
            f.allowed_children = allowed_children_factory(_param_types)
            f.readable_params = ', '.join(map(prettify_converted_type, _param_types))
            f.__params = _param_types
            check(f)
            return f
        return decorator

    def constant(return_type, value):
        @params()
        @rtype(return_type)
        def _const():
            return value
        _const.func_name += '_' + str(value)
        return value

    def lookup_rtype(return_type, convert=True):
        return RTYPES[(convert_type if convert else __id)(return_type)]

    return rtype, params, constant, lookup_rtype


rtype, params, constant, lookup_rtype = __type_annotations_factory()

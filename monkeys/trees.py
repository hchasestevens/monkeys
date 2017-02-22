import random
import collections
import copy

from past.builtins import xrange

from monkeys.typing import lookup_rtype, rtype, params, prettify_converted_type
from monkeys.exceptions import UnsatisfiableType, TreeConstructionError


_REGISTERED_INPUTS = {}


class Node(object):
    def __init__(self, f, allowed_functions=None, selection_strategy=None):
        self.f = f
        self.rtype = f.rtype
        
        allowed_children = self.f.allowed_children()
        if allowed_functions is not None:
            allowed_children = [
                [child for child in child_list if child in allowed_functions] 
                for child_list in 
                allowed_children
            ]
        if not all(allowed_children):
            raise UnsatisfiableType(
                "{} has a parameter that cannot be satisfied.".format(self.f.__name__)
            )
        if selection_strategy is not None:
            child_choices = selection_strategy(
                parent=self.f,
                children=allowed_children,
            )
        else:
            child_choices = (
                random.choice(child_list) 
                for child_list in 
                allowed_children
            )
        self.children = [
            Node(
                choice,
                allowed_functions=allowed_functions,
                selection_strategy=selection_strategy,
            ) 
            for choice in 
            child_choices
        ]
        self.num_children = len(self.children)

    def evaluate(self):
        return self.f(*[child.evaluate() for child in self.children])

    def __str__(self):
        try:
            return self.f.to_string(self.children)
        except AttributeError:
            return '{.f.__name__}({})'.format(self, ', '.join(map(str, self.children)))
        
    def __contains__(self, input_):
        return any(
            child.f == input_ or input_ in child
            for child in self.children
            if isinstance(child, Node)
        )
    
    @property
    def _contains_input(self):
        return isinstance(self.f, Input) or any(
            child._contains_input
            for child in 
            self.children
        )
        
    def __call__(self, input_registry=_REGISTERED_INPUTS, **kwargs):
        """Allow node to be called like a function, setting inputs."""
        for k, v in kwargs.items():
            _REGISTERED_INPUTS[k].set_value(v)
        return self.evaluate()


class Input(object):
    def __init__(self, value, name, registry=_REGISTERED_INPUTS):
        self.value = value
        self.__name__ = name
        registry[name] = self
        
    def set_value(self, value):
        self.value = value
        
    def __call__(self):
        return self.value


def make_input(return_type, initial_value=None, name=''):
    new_input = Input(initial_value, name or 'input_' + str(return_type))
    rtype(return_type)(params()(new_input))
    return new_input


def find_functions(return_type, allowed_functions=None, convert=True):
    functions = lookup_rtype(return_type, convert)
    if allowed_functions is None:
        return functions
    allowable = frozenset(functions) & frozenset(allowed_functions)
    if not allowable:
        raise UnsatisfiableType("No allowable functions satisfying {}.".format(
            (prettify_converted_type if not convert else str)(return_type)
        ))
    return list(allowable)


def build_tree(return_type, allowed_functions=None, convert=True, selection_strategy=None):
    if allowed_functions is not None:
        allowed_functions = frozenset(allowed_functions)
    starting_functions = find_functions(return_type, allowed_functions, convert)
    for __ in xrange(99999):
        try:
            return Node(
                random.choice(starting_functions), 
                allowed_functions=allowed_functions,
                selection_strategy=selection_strategy,
            )
        except RuntimeError:
            pass
    raise TreeConstructionError(
        "Unable to construct program, consider raising recursion depth limit."
    )


CategorizedNode = collections.namedtuple('CategorizedNode', 'node parent index')
GraphEdge = collections.namedtuple('GraphEdge', 'parent children')
TreeInfo = collections.namedtuple(
    'TreeInfo', 
    'nodes_by_rtype depth num_nodes inputs graph_edges'
)

def get_tree_info(tree):
    """Return information about tree structure."""
    frontier = [tree]
    nodes_by_rtype = collections.defaultdict(list)
    depth = 1
    inputs = set()
    graph_edges = []
    while frontier:
        depth += 1
        new_frontier = []
        for node in frontier:
            if not node.children and isinstance(node.f, Input):
                inputs.add(node.f)
            elif node.children:
                graph_edges.append(GraphEdge(
                    parent=node.f,
                    children=tuple(child.f for child in node.children)
                ))
            for i, child in enumerate(node.children):
                nodes_by_rtype[child.rtype].append(
                    CategorizedNode(node=child, parent=node, index=i)
                )
                new_frontier.append(child)
        frontier = new_frontier
    return TreeInfo(
        nodes_by_rtype=nodes_by_rtype,
        depth=depth,
        num_nodes=sum(len(v) for v in nodes_by_rtype.values()),
        inputs=frozenset(inputs),
        graph_edges=graph_edges,
    )


def mutate(tree, allowed_functions=None):
    treeinfo = get_tree_info(tree)
    if not treeinfo.num_nodes:
        return tree
    nodes_by_rtype = treeinfo.nodes_by_rtype
    chosen_rtype = random.choice(list(nodes_by_rtype.keys()))
    chosen_node = random.choice(nodes_by_rtype[chosen_rtype])
    chosen_node.parent.children[chosen_node.index] = build_tree(chosen_rtype, allowed_functions, convert=False)
    return tree


def crossover(first_tree, second_tree=None):
    first_tree_info = get_tree_info(first_tree)
    if second_tree is None:
        sending_tree_info, receiving_tree_info = first_tree_info, first_tree_info
    else:
        sending_tree_info, receiving_tree_info = (first_tree_info, get_tree_info(second_tree))[::random.choice((-1, 1))]
    mutual_rtypes = list(frozenset(sending_tree_info.nodes_by_rtype) & frozenset(receiving_tree_info.nodes_by_rtype))
    if not mutual_rtypes:
        raise UnsatisfiableType("Trees are not compatible.")
    chosen_rtype = random.choice(mutual_rtypes)
    chosen_node = random.choice(receiving_tree_info.nodes_by_rtype[chosen_rtype])
    chosen_replacement = random.choice(sending_tree_info.nodes_by_rtype[chosen_rtype])
    chosen_node.parent.children[chosen_node.index] = copy.deepcopy(chosen_replacement.node)
    if second_tree is None:
        return first_tree
    return first_tree if first_tree_info is receiving_tree_info else second_tree

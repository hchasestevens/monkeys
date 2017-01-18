import random
import collections
import copy
import functools

import numpy

from .typing import lookup_rtype, rtype, params, prettify_converted_type


class UnsatisfiableType(Exception):
    pass


class Node(object):
    def __init__(self, f, allowed_functions=None):
        self.f = f
        self.rtype = f.rtype
        allowed_children = self.f.allowed_children()
        if allowed_functions is not None:
            allowed_children = [[child for child in child_list if child in allowed_functions] for child_list in allowed_children]
        if not all(allowed_children):
            raise UnsatisfiableType("{} has a parameter that cannot be satisfied.".format(self.f.func_name))
        self.children = [Node(random.choice(child_list)) for child_list in allowed_children]
        self.num_children = len(self.children)

    def evaluate(self):
        return self.f(*[child.evaluate() for child in self.children])

    def __str__(self):
        try:
            return self.f.to_string(self.children)
        except AttributeError:
            return '{.f.func_name}({})'.format(self, ', '.join(map(str, self.children)))


class Input(object):
    def __init__(self, value, name):
        self.value = value
        self.func_name = name
    def set(self, value):
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


def build_tree(return_type, allowed_functions=None, convert=True):
    if allowed_functions is not None:
        allowed_functions = frozenset(allowed_functions)
    starting_functions = find_functions(return_type, allowed_functions, convert)
    for __ in xrange(99999):
        try:
            return Node(random.choice(starting_functions), allowed_functions)
        except RuntimeError:
            pass
    raise RuntimeError("Unable to construct program, consider raising recursion depth limit.")


CategorizedNode = collections.namedtuple('CategorizedNode', 'node parent index')
TreeInfo = collections.namedtuple('TreeInfo', 'nodes_by_rtype depth num_nodes inputs')

def get_tree_info(tree):
    frontier = [tree]
    nodes_by_rtype = collections.defaultdict(list)
    depth = 1
    inputs = set()
    while frontier:
        depth += 1
        new_frontier = []
        for node in frontier:
            if not node.children and isinstance(node.f, Input):
                inputs.add(node.f)
            for i, child in enumerate(node.children):
                nodes_by_rtype[child.rtype].append(CategorizedNode(node=child, parent=node, index=i))
                new_frontier.append(child)
        frontier = new_frontier
    return TreeInfo(
        nodes_by_rtype=nodes_by_rtype,
        depth=depth,
        num_nodes=sum(len(v) for v in nodes_by_rtype.itervalues()),
        inputs=frozenset(inputs)
    )


def mutate(tree, allowed_functions=None):
    treeinfo = get_tree_info(tree)
    if not treeinfo.num_nodes:
        return tree
    nodes_by_rtype = treeinfo.nodes_by_rtype
    chosen_rtype = random.choice(nodes_by_rtype.keys())
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


def tournament_select(trees, scoring_fn, selection_size, requires_population=False, cov_parsimony=True, random_parsimony=False, random_parsimony_prob=0.125):
    _scoring_fn = scoring_fn(trees) if requires_population else scoring_fn

    avg_size = 0
    sizes = {}
    
    if cov_parsimony or random_parsimony:
        sizes = {tree: get_tree_info(tree).num_nodes for tree in trees}
        avg_size = sum(sizes.itervalues()) / float(len(sizes))
    
    if random_parsimony:
        # Poli 2003:
        scores = collections.defaultdict(lambda: float('-inf'))
        scores.update({
            tree: _scoring_fn(tree)
            for tree in trees
            if sizes[tree] <= avg_size or random_parsimony_prob < random.random() 
        })
    else:
        scores = {tree: _scoring_fn(tree) for tree in trees}

    if cov_parsimony:
        # Poli & McPhee 2008:
        covariance_matrix = numpy.cov(numpy.array([(sizes[tree], scores[tree]) for tree in trees]).T)
        size_variance = numpy.var([sizes[tree] for tree in trees])
        c = -(covariance_matrix / size_variance)[0, 1]  # 0, 1 should be correlation... is this the wrong way around?
        scores = {tree: score - c * sizes[tree] for tree, score in scores.iteritems()}

    # pseudo-pareto:
    non_neg_inf_scores = [s for s in scores.itervalues() if s != float('-inf')]
    avg_score = sum(non_neg_inf_scores) / float(len(non_neg_inf_scores))
    scores = {
        tree: float('-inf') if score < avg_score and sizes.get(tree, 0) > avg_size else score
        for tree, score in scores.iteritems() 
    }

    while True:
        tree = max(random.sample(trees, selection_size), key=scores.get)
        if scores[tree] == float('-inf'):
            continue
        yield copy.deepcopy(tree)


def next_generation(trees, scoring_fn, select_fn=functools.partial(tournament_select, selection_size=10), crossover_rate=0.90, mutation_rate=0.01):
    selector = select_fn(trees, scoring_fn)
    pop_size = len(trees)
    
    new_pop = []
    for __ in xrange(pop_size):
        if random.random() <= crossover_rate:
            for __ in xrange(99999):
                try:
                    new_pop.append(crossover(next(selector), next(selector)))
                    break
                except UnsatisfiableType:
                    pass
            else:
                raise UnsatisfiableType("Trees are not compatible.")

        elif random.random() <= mutation_rate / (1 - crossover_rate):
            new_pop.append(mutate(next(selector)))

        else:
            new_pop.append(next(selector))

    return new_pop

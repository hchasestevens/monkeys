"""Search functionality and objective function tooling."""

from __future__ import print_function

import ast
import sys
import copy
import random
import inspect
import functools
import contextlib
import collections

import numpy
from six import iteritems, itervalues
from past.builtins import xrange

from monkeys.trees import get_tree_info, build_tree, crossover, mutate
from monkeys.exceptions import UnsatisfiableType


def tournament_select(trees, scoring_fn, selection_size, requires_population=False, cov_parsimony=False, random_parsimony=True, random_parsimony_prob=0.33, score_callback=None):
    _scoring_fn = scoring_fn(trees) if requires_population else scoring_fn

    avg_size = 0
    sizes = {}
    
    if cov_parsimony or random_parsimony:
        sizes = {tree: get_tree_info(tree).num_nodes for tree in trees}
        avg_size = sum(itervalues(sizes)) / float(len(sizes))
    
    if random_parsimony:
        # Poli 2003:
        scores = collections.defaultdict(lambda: -sys.maxsize)
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
        scores = {tree: score - c * sizes[tree] for tree, score in iteritems(scores)}

    # pseudo-pareto:
    non_neg_inf_scores = [s for s in itervalues(scores) if s != -sys.maxsize]
    try:
        avg_score = sum(non_neg_inf_scores) / float(len(non_neg_inf_scores))
    except ZeroDivisionError:
        avg_score = -sys.maxsize
    scores = {
        tree: -sys.maxsize if score < avg_score and sizes.get(tree, 0) > avg_size else score
        for tree, score in iteritems(scores)
    }
    if callable(score_callback):
        score_callback(scores)

    while True:
        tree = max(
            random.sample(trees, selection_size),
            key=lambda t: scores.get(t, -sys.maxsize)
        )
        if scores.get(tree, -sys.maxsize) == -sys.maxsize:
            try:
                new_tree = build_tree_to_requirements(scoring_fn)
            except UnsatisfiableType:
                continue
        else:
            try:
                with recursion_limit(1500):
                    new_tree = copy.deepcopy(tree)
            except RuntimeError:
                try:
                    new_tree = build_tree_to_requirements(scoring_fn)
                except UnsatisfiableType:
                    continue
        yield new_tree
        
        
def pre_evaluate(scoring_fn):
    """
    Evaluate trees before passing to the scoring function.
    """
    @functools.wraps(scoring_fn)
    def wrapper(tree):
        try:
            evaluated_tree = tree.evaluate()
        except Exception:
            return -sys.maxsize
        return scoring_fn(evaluated_tree)
    return wrapper


def minimize(scoring_fn):
    """Minimize score."""
    @functools.wraps(scoring_fn)
    def wrapper(tree):
        return -scoring_fn(tree)
    return wrapper


class AssertionReplacer(ast.NodeTransformer):
    """Transformer used in score_on_assertions."""
    
    def __init__(self, score_var_name):
        self.score_var_name = score_var_name
        self.max_score = 0
        
    def visit_Assert(self, node):
        """Replace assertions with augmented assignments."""
        self.max_score += 1
        return ast.AugAssign(
            op=ast.Add(),
            target=ast.Name(
                id=self.score_var_name,
                ctx=ast.Store()
            ),
            value=ast.Call(
                args=[node.test],
                func=ast.Name(
                    id='bool',
                    ctx=ast.Load()
                ),
                keywords=[],
                kwargs=None,
                starargs=None
            )
        )


def assertions_as_score(scoring_fn):
    """
    Create a scoring function from a multi-assert test, allotting
    one point per successful assertion.
    
    Nota bene: if used in conjunction with other decorators, must
    be the first decorator applied to the function.
    """
    score_var_name = '__score__'
    
    function_source = inspect.getsource(scoring_fn)
        
    fn_ast, = ast.parse(function_source).body
    fn_ast.body.insert(
        0,
        ast.Assign(
            targets=[ast.Name(
                id=score_var_name,
                ctx=ast.Store()
            )],
            value=ast.Num(n=0)
        )
    )
    fn_ast.body.append(
        ast.Return(
            value=ast.Name(
                id=score_var_name,
                ctx=ast.Load()
            )
        )
    )
    fn_ast.decorator_list = []
    assertion_replacer = AssertionReplacer(score_var_name)
    fn_ast = assertion_replacer.visit(fn_ast)
    
    code = compile(
        ast.fix_missing_locations(
            ast.Module(body=[fn_ast])
        ), 
        '<string>', 
        'exec'
    )
    context = {}
    exec(code, scoring_fn.__globals__, context)
    new_scoring_fn, = context.values()
    new_scoring_fn.__max_score = assertion_replacer.max_score
    
    return functools.wraps(scoring_fn)(new_scoring_fn)


def next_generation(trees, scoring_fn, select_fn=functools.partial(tournament_select, selection_size=25), crossover_rate=0.80, mutation_rate=0.01, score_callback=None):
    selector = select_fn(trees, scoring_fn, score_callback=score_callback)
    pop_size = len(trees)
    
    new_pop = [max(trees, key=scoring_fn)]
    for __ in xrange(pop_size - 1):
        if random.random() <= crossover_rate:
            for __ in xrange(99999):
                try:
                    new_pop.append(crossover(next(selector), next(selector)))
                    break
                except (UnsatisfiableType, RuntimeError):
                    continue
            else:
                new_pop.append(build_tree_to_requirements(scoring_fn))

        elif random.random() <= mutation_rate / (1 - crossover_rate):
            new_pop.append(mutate(next(selector)))

        else:
            new_pop.append(next(selector))

    return new_pop


def require(*inputs):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(tree):
            if not all(i in tree for i in inputs):
                return -sys.maxsize
            return fn(tree)
        wrapper.required_inputs = inputs
        return wrapper
    return decorator


@contextlib.contextmanager
def recursion_limit(limit):
    orig_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(limit)
    try:
        yield
    finally:
        sys.setrecursionlimit(orig_limit)
                
                
def build_tree_to_requirements(scoring_function):
    params = getattr(scoring_function, '__params', ())
    if len(params) != 1:
        raise ValueError("Scoring function must accept a single parameter.")
    return_type, = params
    
    for __ in xrange(9999):
        with recursion_limit(500):
            tree = build_tree(return_type, convert=False)
        requirements = getattr(scoring_function, 'required_inputs', ())
        if not all(req in tree for req in requirements):
            continue
        return tree
    
    raise UnsatisfiableType("Could not meet input requirements.")
    

def optimize(scoring_function, population_size=250, iterations=25, build_tree=build_tree, next_generation=next_generation, show_scores=True):  
    print("Creating initial population of {}.".format(population_size))
    sys.stdout.flush()
    
    population = []
    for __ in xrange(population_size):
        try:
            tree = build_tree_to_requirements(scoring_function)
            population.append(tree)
        except UnsatisfiableType:
            raise UnsatisfiableType(
                "Could not meet input requirements. Found only {} satisfying trees.".format(
                    len(population)
                )
            )
    best_tree = [random.choice(population)]
    early_stop = []
    
    def score_callback(iteration, scores):
        if not show_scores:
            return
        
        non_failure_scores = [
            score 
            for score in 
            scores.values()
            if score != -sys.maxsize
        ]
        try:
            average_score = sum(non_failure_scores) / len(non_failure_scores)
        except ZeroDivisionError:
            average_score = -sys.maxsize
        best_score = max(scores.values())
        
        best_tree.append(max(scores, key=scores.get))
        
        print("Iteration {}:\tBest: {:.2f}\tAverage: {:.2f}".format(
            iteration + 1,
            best_score,
            average_score,
        ))
        sys.stdout.flush()
        
        if best_score == getattr(scoring_function, '__max_score', None):
            early_stop.append(True)
    
    print("Optimizing...")
    with recursion_limit(600):
        for iteration in xrange(iterations):
            callback = functools.partial(score_callback, iteration)
            population = next_generation(population, scoring_function, score_callback=callback)
            if early_stop:
                break
        
    best_tree = max(best_tree, key=scoring_function)
    return best_tree
    
        

"""Tools for diagnosing errors."""

from __future__ import print_function

import functools
import operator
from collections import defaultdict, OrderedDict

from six import iteritems
from past.builtins import xrange

from monkeys.typing import REGISTERED_TYPES, lookup_rtype
from monkeys.trees import build_tree, get_tree_info
from monkeys.exceptions import UnsatisfiableConstraint
from monkeys.aco import AntColony, DEFAULT_PHEROMONE_TYPE


class Diagnosis(object):
    """Report of diagnostic results."""
    
    def __init__(self, exceptions, ant_colony):
        self.exception_examples = exceptions
        self.exceptions = list(exceptions.keys())
        
        self.minimal_reproductions = {
            exception: min(
                trees,
                key=lambda t: get_tree_info(t).num_nodes
            )
            for exception, trees in
            iteritems(exceptions)
        }
        
        edge_weightings = defaultdict(dict)  # {exception: {edge: weight}}
        for parent, child_combination, exception, concentration in ant_colony:
            if exception not in exceptions:
                continue
            pretty_edge = '({}) -> {}'.format(
                ', '.join(child.__name__ for child in child_combination),
                parent.__name__,
            )
            edge_weightings[exception][pretty_edge] = concentration
        self.edge_weightings = {
            exception: OrderedDict(sorted(
                iteritems(weightings),
                key=operator.itemgetter(1),
                reverse=True
            ))
            for exception, weightings in
            iteritems(edge_weightings)
        }
        
    def show_report(self, top=3):
        for exception in self.exceptions:
            print('{}:'.format(exception))
            edge_weightings = iteritems(self.edge_weightings[exception])
            for __, (edge, weight) in zip(xrange(top), edge_weightings):
                print('    {:.2f} | {}'.format(weight, edge))
            

def diagnose(target_type, test=None, sample_size=250):
    """
    Identify and localize exceptions encountered when evaluating
    trees of the specified target type. If a test is supplied, this
    will also be applied to evaluated trees.
    """
    colony = AntColony({
        rtype: lookup_rtype(rtype, convert=False)
        for rtype in 
        REGISTERED_TYPES
    })
    
    if test is None:
        test = lambda x: None
    
    encountered_exceptions = defaultdict(list)
    print("Collecting exception sample...")
    with colony.iteration():
        for __ in range(sample_size):
            tree = build_tree(target_type)
            try:
                test(tree.evaluate())
            except Exception as e:
                exception = repr(e)
                encountered_exceptions[exception].append(tree)
            else:
                exception = DEFAULT_PHEROMONE_TYPE
            colony.deposit({tree: 1.0}, pheromone_type=exception)
        
    if not encountered_exceptions:
        error_message = "Could not find any exceptions after {} trials."
        raise UnsatisfiableConstraint(error_message.format(sample_size))
        
    print("Discovered {} distinct exceptions.".format(len(encountered_exceptions)))
    
    print("Reproducing exceptions...")
    for __ in xrange(sample_size):
        with colony.iteration():
            for exception in encountered_exceptions:
                colony_select = functools.partial(
                    colony.select,
                    pheromone_type=exception
                )
                tree = build_tree(
                    target_type,
                    selection_strategy=colony_select
                )
                try:
                    test(tree.evaluate())
                except Exception as e:
                    exception = repr(e)
                else:
                    exception = None
                if exception not in encountered_exceptions:
                    colony.deposit(
                        {tree: 1.0}, 
                        pheromone_type=DEFAULT_PHEROMONE_TYPE
                    )
                    continue
                encountered_exceptions[exception].append(tree)
                colony.deposit({tree: 1.0}, pheromone_type=exception)
                    
    diagnosis = Diagnosis(
        exceptions=encountered_exceptions,
        ant_colony=colony
    )
    print("Done.")
    return diagnosis

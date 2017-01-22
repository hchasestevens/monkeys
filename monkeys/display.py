"""
Visualization tooling.
"""

from collections import defaultdict

import graphviz

from monkeys.typing import REGISTERED_TYPES, lookup_rtype, prettify_converted_type


def type_graph(simplify=False):
    """
    Render graph of current type system.
    """
    graph = graphviz.Digraph(format='svg')
    graph.node(
        u'\u03b5', 
        shape='circle',
        style='dotted',
    )
    
    edge_pairs = set()
    def add_edge(*pair):
        if pair in edge_pairs:
            return
        graph.edge(*pair)
        edge_pairs.add(pair)
        
    simplified_graph = defaultdict(set)
    for t in REGISTERED_TYPES:
        targeting_functions = lookup_rtype(t, convert=False)
        pretty_t = prettify_converted_type(t)
        for targeting_function in targeting_functions:

            params = targeting_function.readable_param_list

            if not params:
                add_edge(
                    u'\u03b5',
                    pretty_t
                )
                continue
                
            for param in params:
                simplified_graph[param].add(pretty_t)
            
            if simplify:
                # pretend these can go directly to the return type
                for param in params:
                    add_edge(
                        param,
                        pretty_t
                    )
                continue
                
            elif len(params) > 1:
                # show composition of constructed type from constituents
                graph.node(
                    targeting_function.readable_params, 
                    shape='rect', 
                    style='dashed',
                )
                for param in params:
                    add_edge(
                        param,
                        targeting_function.readable_params
                    )
                    
            add_edge(targeting_function.readable_params, pretty_t)
            
    end_states = {
        t
        for t in
        map(prettify_converted_type, REGISTERED_TYPES)
        if not simplified_graph[t]
        or simplified_graph[t] == {t}
    }
    for end_state in end_states:
        graph.node(
            end_state, 
            peripheries='2',
        )
    
    return graph
                    


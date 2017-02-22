import ast
import copy
import inspect
import functools

import astor


class NameReplacer(ast.NodeTransformer):
    def __init__(self, replacements):
        self.replacements = replacements
        
    def visit_Name(self, node):
        if node.id in self.replacements:
            replacement = self.replacements[node.id]
            if isinstance(replacement, list):
                if len(replacement) > 1:
                    return ast.If(
                        test=ast.Num(n=1),
                        body=replacement,
                        orelse=[]
                    )
                return replacement[0]
            return replacement
        return self.generic_visit(node)
    
    
def quoted(fn):
    """
    Return the code literal represented in the function body.
    """
    src = inspect.getsource(fn)
    return ast.parse(src).body[0].body


def quoted_template(fn):
    """
    Return a function which, supplied with AST nodes, will
    populate and return the specified template body.
    """
    fn_node = ast.parse(inspect.getsource(fn)).body[0]
    argnames = [
        name.id
        if hasattr(name, 'id')
        else name.arg
        for name in
        fn_node.args.args
    ]
        
    @functools.wraps(fn)
    def wrapper(*args):
        argdict = dict(zip(argnames, args))
        populated_template = NameReplacer(argdict).visit(copy.deepcopy(fn_node))
        # round-robin AST -> source -> AST conversion to fix type mismatches
        return ast.parse(
            astor.to_source(
                ast.Module(
                    body=populated_template.body
                )
            )
        ).body
    
    return wrapper
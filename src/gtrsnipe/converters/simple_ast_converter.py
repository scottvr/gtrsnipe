import ast
import inspect
from typing import List
from ..core.operations import Operation, GuitarOperation

class ASTToOperationsConverter:
    def __init__(self):
        self.current_beat = 0.0
        self.operations: List[GuitarOperation] = []
    
    def convert(self, func) -> List[GuitarOperation]:
        """Convert a Python function to guitar operations"""
        source = inspect.getsource(func)
        tree = ast.parse(source)
        
        # Find and process function definition
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._process_node(node)
                break
                
        return self.operations
    
    def _process_node(self, node: ast.AST):
        match node:
            case ast.BinOp():
                self._process_binary_operation(node)
            case ast.Compare():
                self._process_comparison(node)
            case ast.Assign():
                self._process_assignment(node)
            case ast.If():
                self._process_if_statement(node)
            case _:
                for child in ast.iter_child_nodes(node):
                    self._process_node(child)
    
import ast
import inspect
import textwrap
from typing import Dict, List, Tuple, Optional
from .cpu import GuitarCPU
from .program import GuitarProgram
from ..core.operations import Operation, GuitarOperation
from ..utils.fretboard import FretPosition

class VariableMapping:
    def __init__(self):
        self.current_string = 0
        self.current_fret = 0
        self.vars: Dict[str, FretPosition] = {}
    
    def allocate(self, var_name: str) -> FretPosition:
        """Allocate a new fret position for a variable"""
        if var_name in self.vars:
            return self.vars[var_name]
            
        pos = FretPosition(self.current_string, self.current_fret)
        self.vars[var_name] = pos
        
        # Move to next position
        self.current_fret += 1
        if self.current_fret > 12:  # Use first 12 frets for variables
            self.current_fret = 0
            self.current_string += 1
            
        return pos

class ASTToGuitarCompiler:
    def __init__(self, cpu: GuitarCPU):
        self.cpu = cpu
        self.vars = VariableMapping()
        self.current_beat = 0.0
        self.operations: List[tuple[float, GuitarOperation]] = []
        self.loop_starts: List[float] = []  # Stack for loop start beats
        self.loop_ends: List[float] = []    # Stack for loop end beats
        
    def compile_function(self, func) -> GuitarProgram:
        """Compile a Python function to guitar operations"""
        program = GuitarProgram(self.cpu)
        tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
        print(f"AST: {ast.dump(tree, indent=2)}")  # Debug AST
        
        # Find and process function definition
        for node in ast.walk(tree):
            print(f'node: {node}')
            if isinstance(node, ast.FunctionDef):
                print(f'processing node...')
                self._process_node(node, program)
                break
                
        return program

    def _process_operation(self, node: ast.AST) -> List[Tuple[str, str]]:
        """Process mathematical and logical operations"""
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in self.operation_patterns:
                progression = ' -> '.join(self.operation_patterns[op_type])
                return [(f"{progression} [sustain]", f"Process {op_type.__name__} operation")]
        return []

    def _add_op(self, op: GuitarOperation):
        self.operations.append((self.current_beat, op))
        self.current_beat += 1.0

    def _process_node(self, node: ast.AST, program: GuitarProgram):
        """Process an AST node and generate guitar operations"""
        print(f"proc_node...: {ast.dump(node, indent=2)}")  # Debug AST
        # Process based on node type
        match node:
            case ast.FunctionDef():
                print(f'ast: functiondef...')
                for stmt in node.body:
                    self._process_node(stmt, program)
                    
            case ast.Assign():
                print(f'ast: assign...')
                if isinstance(node.targets[0], ast.Tuple):
                    # Handle tuple unpacking (a, b = x, y)
                    if isinstance(node.value, ast.Tuple):
                        right_values = []
                        for val in node.value.elts:
                            right_values.append(self._process_expr(val))
                        
                        for target, val_ops in zip(node.targets[0].elts, right_values):
                            if isinstance(target, ast.Name):
                                target_pos = self.vars.allocate(target.id)
                                for op in val_ops:
                                    self._add_op(op)
                                self._add_op(GuitarOperation(
                                    operation=Operation.STORE,
                                    string=target_pos.string,
                                    fret=target_pos.fret
                                ))
                
            case ast.For():
                print(f'ast: for...')
                if (isinstance(node.iter, ast.Call) and 
                    isinstance(node.iter.func, ast.Name) and 
                    node.iter.func.id == 'range'):
                    
                    counter_pos = self.vars.allocate(node.target.id)
                    start_ops = self._process_expr(node.iter.args[0])
                    end_ops = self._process_expr(node.iter.args[1])
                    
                    # Initialize counter
                    for op in start_ops:
                        self._add_op(op)
                    self._add_op(GuitarOperation(
                        operation=Operation.STORE,
                        string=counter_pos.string,
                        fret=counter_pos.fret
                    ))
                    
                    loop_start = self.current_beat
                    
                    # Process loop body
                    for stmt in node.body:
                        self._process_node(stmt, program)
                    
                    # Increment counter and check condition
                    self._add_op(GuitarOperation(
                        operation=Operation.LOAD,
                        string=counter_pos.string,
                        fret=counter_pos.fret
                    ))
                    self._add_op(GuitarOperation(
                        operation=Operation.ADD,
                        string=counter_pos.string,
                        fret=1
                    ))
                    self._add_op(GuitarOperation(
                        operation=Operation.STORE,
                        string=counter_pos.string,
                        fret=counter_pos.fret
                    ))
                    
                    # Compare to end value
                    for op in end_ops:
                        self._add_op(op)
                    self._add_op(GuitarOperation(
                        operation=Operation.COMPARE,
                        string=counter_pos.string,
                        fret=counter_pos.fret
                    ))
                    self._add_op(GuitarOperation(
                        operation=Operation.JUMP,
                        string=0,
                        fret=int(loop_start),
                        value='less'
                    ))
            
            case ast.For():
                # Initialize loop variable
                if isinstance(node.target, ast.Name):
                    loop_var_pos = self.vars.allocate(node.target.id)
                    
                # Process range() arguments
                if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
                    if node.iter.func.id == 'range':
                        # Get start and end values
                        start_ops = self._process_expression(node.iter.args[0])  # 2
                        end_ops = self._process_expression(node.iter.args[1])    # n
                        
                        # Add operations for initializing loop counter
                        for op in start_ops:
                            program.add_instruction(self.current_beat, op)
                            self.current_beat += 0.25
                        
                        # Store start value to loop counter
                        program.add_instruction(
                            self.current_beat,
                            GuitarOperation(
                                operation=Operation.STORE,
                                string=loop_var_pos.string,
                                fret=loop_var_pos.fret
                            )
                        )
                        self.current_beat += 0.25
                        
                        # Remember loop start point
                        loop_start = self.current_beat
                        
                        # Process loop body
                        for stmt in node.body:
                            self._process_node(stmt, program)
                        
                        # Add loop control operations
                        program.add_instruction(
                            self.current_beat,
                            GuitarOperation(
                                operation=Operation.LOAD,
                                string=loop_var_pos.string,
                                fret=loop_var_pos.fret
                            )
                        )
                        self.current_beat += 0.25
                        
                        # Increment loop counter
                        program.add_instruction(
                            self.current_beat,
                            GuitarOperation(
                                operation=Operation.ADD,
                                string=loop_var_pos.string,
                                fret=1  # Add 1 to increment
                            )
                        )
                        self.current_beat += 0.25
                        
                        # Compare to end value
                        for op in end_ops:
                            program.add_instruction(self.current_beat, op)
                            self.current_beat += 0.25
                        program.add_instruction(
                            self.current_beat,
                            GuitarOperation(
                                operation=Operation.COMPARE,
                                string=loop_var_pos.string,
                                fret=loop_var_pos.fret
                            )
                        )
                        self.current_beat += 0.25
                        
                        # Jump back if not done
                        program.add_instruction(
                            self.current_beat,
                            GuitarOperation(
                                operation=Operation.JUMP,
                                string=0,  # Control operations use string 0
                                fret=loop_start,
                                value='less'  # Jump if counter < end
                            )
                        )
                        self.current_beat += 0.25

            case ast.Assign():
                print('in assign...')
                if isinstance(node.targets[0], ast.Name):
                    print('in isins0...')
                    # Simple assignment: x = value
                    target = node.targets[0].id
                    target_pos = self.vars.allocate(target)
                    
                    # Process the value expression
                    value_ops = self._process_expression(node.value)
                    for op in value_ops:
                        program.add_instruction(self.current_beat, op)
                        self.current_beat += 0.25
                    
                    # Store result
                    program.add_instruction(
                        self.current_beat,
                        GuitarOperation(
                            operation=Operation.STORE,
                            string=target_pos.string,
                            fret=target_pos.fret
                        )
                    )
                    self.current_beat += 0.25
                    
                elif isinstance(node.targets[0], ast.Tuple):
                    # Handle tuple unpacking: a, b = x, y
                    if not isinstance(node.value, ast.Tuple):
                        raise ValueError("Expected tuple on right side of unpacking")
                    
                    # Process all right-side expressions first
                    right_values = []
                    for value in node.value.elts:
                        value_ops = self._process_expression(value)
                        right_values.append(value_ops)
                    
                    # Generate operations to store each value
                    for target, value_ops in zip(node.targets[0].elts, right_values):
                        if isinstance(target, ast.Name):
                            target_pos = self.vars.allocate(target.id)
                            # Store the computed value
                            for op in value_ops:
                                program.add_instruction(self.current_beat, op)
                                self.current_beat += 0.25
                            program.add_instruction(
                                self.current_beat,
                                GuitarOperation(
                                    operation=Operation.STORE,
                                    string=target_pos.string,
                                    fret=target_pos.fret
                                )
                            )
                            self.current_beat += 0.25
                        else:
                            raise ValueError(f"Unsupported tuple target type: {type(target)}")
                else:
                    raise ValueError(f"Unsupported assignment target type: {type(node.targets[0])}")
            case _:
                for child in ast.iter_child_nodes(node):
                    self._process_node(child, program)

    def _process_expr(self, node: ast.AST) -> List[GuitarOperation]:
        match node:
            case ast.Name():
                pos = self.vars.allocate(node.id)
                return [GuitarOperation(
                    operation=Operation.LOAD,
                    string=pos.string,
                    fret=pos.fret
                )]
                
            case ast.Constant():
                pos = self.vars.allocate(f"const_{node.value}")
                return [GuitarOperation(
                    operation=Operation.LOAD,
                    string=pos.string,
                    fret=pos.fret,
                    value=node.value
                )]
                
            case ast.BinOp():
                if isinstance(node.op, ast.Add):
                    left = self._process_expr(node.left)
                    right = self._process_expr(node.right)
                    ops = []
                    ops.extend(left)
                    ops.extend(right)
                    last_pos = (right[-1].string, right[-1].fret)
                    ops.append(GuitarOperation(
                        operation=Operation.ADD,
                        string=last_pos[0],
                        fret=last_pos[1]
                    ))
                    return ops
                
            case ast.Compare():
                if isinstance(node.ops[0], (ast.Lt, ast.LtE)):
                    left = self._process_expr(node.left)
                    right = self._process_expr(node.comparators[0])
                    ops = []
                    ops.extend(left)
                    ops.extend(right)
                    last_pos = (right[-1].string, right[-1].fret)
                    ops.append(GuitarOperation(
                        operation=Operation.COMPARE,
                        string=last_pos.string,
                        fret=last_pos.fret
                    ))
                    return ops
                
        return []

    def compile_operations(self, operations: List[GuitarOperation]) -> List[GuitarOperation]:
        """Compile operations into optimized guitar instructions"""
        compiled = []
        previous_position = None
        
        for op in operations:
            # Find optimal position for this operation
            if previous_position:
                optimal_pos = self.fretboard.find_optimal_position(
                    op.string, op.fret, op.technique, previous_position
                )
                op.string = optimal_pos.string
                op.fret = optimal_pos.fret
            
            # Assign timing
            op.beat = self.current_beat
            self.current_beat += self._get_operation_duration(op)
            
            compiled.append(op)
            previous_position = FretPosition(op.string, op.fret)
        
        return compiled
    
    def _get_operation_duration(self, operation: GuitarOperation) -> float:
        """Calculate duration needed for an operation"""
        duration_map = {
            Operation.LOAD: 1.0,
            Operation.STORE: 1.0,
            Operation.ADD: 2.0,  # Hammer-on takes longer
            Operation.SUB: 2.0,  # Pull-off takes longer
            Operation.MUL: 3.0,  # Bends take even longer
            Operation.DIV: 2.0,
            Operation.COMPARE: 1.0,
            Operation.JUMP: 1.0
        }
        return duration_map.get(operation.operation, 1.0)

    def _process_expression(self, node: ast.AST) -> List[GuitarOperation]:
        """Convert an expression to guitar operations"""
        print(f"Processing expression: {ast.dump(node)}")  # Debug expressions
        operations = []
        
        match node:
            case ast.BinOp():
                # Process left operand
                operations.extend(self._process_expression(node.left))
                
                # Process right operand and operation
                match type(node.op):
                    case ast.Add:
                        op = Operation.ADD
                    case ast.Sub:
                        op = Operation.SUB
                    case ast.Mult:
                        op = Operation.MUL
                    case ast.Div:
                        op = Operation.DIV
                    case _:
                        raise ValueError(f"Unsupported operation: {type(node.op)}")
                
                right_ops = self._process_expression(node.right)
                operations.extend(right_ops)
                
                # Add the operation
                if right_ops:
                    last_pos = right_ops[-1].string, right_ops[-1].fret
                    operations.append(
                        GuitarOperation(
                            operation=op,
                            string=last_pos.string,
                            fret=last_pos.fret
                        )
                    )
                
            case ast.Name():
                # Load variable value
                var_pos = self.vars.allocate(node.id)
                operations.append(
                    GuitarOperation(
                        operation=Operation.LOAD,
                        string=var_pos.string,
                        fret=var_pos.fret
                    )
                )
                
            case ast.Num():
                # Load constant value
                const_pos = self.vars.allocate(f"const_{node.n}")
                operations.append(
                    GuitarOperation(
                        operation=Operation.LOAD,
                        string=const_pos.string,
                        fret=const_pos.fret,
                        value=node.n
                    )
                )
                
            case ast.Constant():
                # Return a list containing the single operation
                const_pos = self.vars.allocate(f"const_{node.value}")
                return [GuitarOperation(
                    operation=Operation.LOAD,
                    string=const_pos.string,
                    fret=const_pos.fret,
                    value=node.value
                )]
                
            case ast.Compare():
                # Process left side
                operations.extend(self._process_expression(node.left))
                
                # Process comparisons
                for op, right in zip(node.ops, node.comparators):
                    right_ops = self._process_expression(right)
                    operations.extend(right_ops)
                    
                    # Add comparison operation
                    if right_ops:
                        last_pos = right_ops[-1].string, right_ops[-1].fret
                        operations.append(
                            GuitarOperation(
                                operation=Operation.COMPARE,
                                string=last_pos.string,
                                fret=last_pos.fret
                            )
                        )
        
        return operations
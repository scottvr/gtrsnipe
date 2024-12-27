import ast
import inspect
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from gtrsnipe import MusicalEvent, TabFormatter, GuitarPositionMapper, GuitarCPU, GuitarProgram, MidiToTabConverter, TimeSignature, ASTToGuitarCompiler, GuitarOperation, Operation

class MinimalCompiler:
    def __init__(self):
        self.vars: Dict[str, tuple[int, int]] = {}  # name -> (string, fret)
        self.current_string = 0
        self.current_fret = 0
        self.current_beat = 0.0
        self.operations: List[tuple[float, GuitarOperation]] = []
        
    def allocate_var(self, name: str) -> tuple[int, int]:
        if name not in self.vars:
            self.vars[name] = (self.current_string, self.current_fret)
            self.current_fret += 1
            if self.current_fret > 12:
                self.current_fret = 0
                self.current_string += 1
        return self.vars[name]
    
    def compile(self, func) -> List[tuple[float, GuitarOperation]]:
        source = textwrap.dedent(inspect.getsource(func))
        tree = ast.parse(source)
        self._process_node(tree.body[0])
        return Gelf.operations
    
    def _add_op(self, op: GuitarOperation):
        self.operations.append((self.current_beat, op))
        self.current_beat += 1.0
    
    def _process_node(self, node: ast.AST):
        match node:
            case ast.FunctionDef():
                print(f'ast: functiondef...')
                for stmt in node.body:
                    self._process_node(stmt)
                    
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
                                target_pos = self.allocate_var(target.id)
                                for op in val_ops:
                                    self._add_op(op)
                                self._add_op(GuitarOperation(
                                    operation=Operation.STORE,
                                    string=target_pos[0],
                                    fret=target_pos[1]
                                ))
                
            case ast.For():
                print(f'ast: for...')
                if (isinstance(node.iter, ast.Call) and 
                    isinstance(node.iter.func, ast.Name) and 
                    node.iter.func.id == 'range'):
                    
                    counter_pos = self.allocate_var(node.target.id)
                    start_ops = self._process_expr(node.iter.args[0])
                    end_ops = self._process_expr(node.iter.args[1])
                    
                    # Initialize counter
                    for op in start_ops:
                        self._add_op(op)
                    self._add_op(GuitarOperation(
                        operation=Operation.STORE,
                        string=counter_pos[0],
                        fret=counter_pos[1]
                    ))
                    
                    loop_start = self.current_beat
                    
                    # Process loop body
                    for stmt in node.body:
                        self._process_node(stmt)
                    
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
                        string=counter_pos[0],
                        fret=counter_pos[1]
                    ))
                    self._add_op(GuitarOperation(
                        operation=Operation.JUMP,
                        string=0,
                        fret=int(loop_start),
                        value='less'
                    ))
            
            case ast.Return():
                print(f'ast: ret...')
                if node.value:
                    for op in self._process_expr(node.value):
                        self._add_op(op)
    
    def _process_expr(self, node: ast.AST) -> List[GuitarOperation]:
        match node:
            case ast.Name():
                pos = self.allocate_var(node.id)
                return [GuitarOperation(
                    operation=Operation.LOAD,
                    string=pos[0],
                    fret=pos[1]
                )]
                
            case ast.Constant():
                pos = self.allocate_var(f"const_{node.value}")
                return [GuitarOperation(
                    operation=Operation.LOAD,
                    string=pos[0],
                    fret=pos[1],
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
                        string=last_pos[0],
                        fret=last_pos[1]
                    ))
                    return ops
                
        return []

def operation_to_musical_event(beat: float, op: GuitarOperation) -> MusicalEvent:
    technique_map = {
        Operation.LOAD: 'tap',
        Operation.STORE: 'pick',
        Operation.ADD: 'hammer-on',
        Operation.COMPARE: 'harmonic',
        Operation.JUMP: 'slide'
    }
    
    return MusicalEvent(
        time=beat,
        duration=0.125,
        pitch=0,
        velocity=80 if op.operation == Operation.ADD else 60,
        string=op.string,
        fret=op.fret,
        technique=technique_map.get(op.operation, 'pick')
    )

##
#from gtrsnipe import MidiToTabConverter, TimeSignature, FretPosition, Technique, TabFormatter, GuitarPositionMapper, GuitarCPU, GuitarProgram, ASTToGuitarCompiler
from gtrsnipe.computer.program import create_musical_events

def test_conversion(midi_file: str):
    # Create converter with default settings
    converter = MidiToTabConverter(
        default_tempo=120.0,
        default_time_sig=TimeSignature(4, 4)
    )
    mapper = GuitarPositionMapper()
    formatter = TabFormatter()
    
    # Convert MIDI to events
    events, tempo, time_sig = converter.convert(midi_file)
    
    # Map to guitar positions
    guitar_events = mapper.map_events(events)
    
    # Create and format tab
    score = formatter.create_tab_from_events(guitar_events, tempo, (time_sig.numerator, time_sig.denominator))
    return formatter.format_score(score)

def fibonacci_program(cpu: GuitarCPU) -> GuitarProgram:
    program = GuitarProgram(cpu)
    
    # Initialize first two numbers
    program.add_instruction(0, GuitarOperation(
        operation=Operation.LOAD,
        string=0,
        fret=0,
        value=0
    ))
    program.add_instruction(1, GuitarOperation(
        operation=Operation.STORE,
        string=1,
        fret=0
    ))
    
    # Add fibonacci sequence operations
    for i in range(2, 8, 2):
        # Load previous number
        program.add_instruction(i, GuitarOperation(
            operation=Operation.LOAD,
            string=0,
            fret=i-1
        ))
        # Add numbers
        program.add_instruction(i+0.5, GuitarOperation(
            operation=Operation.ADD,
            string=1,
            fret=i-2
        ))
        # Store result
        program.add_instruction(i+1, GuitarOperation(
            operation=Operation.STORE,
            string=0,
            fret=i
        ))
    
    return program

def fibonacci_function():
    if n <= 1:
        return n
    a, b = 0, 1
    for i in range(2, n):
        a, b = b, a + b
    return b

def compile_and_run(func) -> str:
    cpu = GuitarCPU()
    compiler = ASTToGuitarCompiler(cpu)
    #compiler = MinimalCompiler()
    program = compiler.compile_function(func)
    print(f'pr: {dir(program)}') 
    print(f'pr: {program}') 
    # Compile to timed instructions
    timed_instructions = program.compile(execute=True)
    print(f'ti: {dir(timed_instructions)}') 
    print(f'ti: {timed_instructions}') 
    
    # Convert to musical events
    events = create_musical_events(program,timed_instructions)
    print(f'ev: {dir(events)}') 
    print(f'ev: {events}') 
    
    # Generate tab
    formatter = TabFormatter()
    score = formatter.create_tab_from_events(
        events, program.tempo, program.time_signature
    )
    return formatter.format_score(score)


def fizzbuzz(n):
    if n % 3 == 0 and n % 5 == 0:
        return "FizzBuzz"
    elif n % 3 == 0:
        return "Fizz"
    elif n % 5 == 0:
        return "Buzz"
    return n


print("###################################### TEST 1 - midi input ###################################")
print(test_conversion("input.mid"))


print("###################################### TEST 2 - fizzbuzz ast transpile ###################################")
print(compile_and_run(fizzbuzz))

print("###################################### TEST 3 - fibonacci ast transpile ###################################")
gtrCPU = GuitarCPU()
compiler = ASTToGuitarCompiler(gtrCPU)
operations = compiler.compile_function(fibonacci_function)
mapper = GuitarPositionMapper()
score = ""

print(f'ops: {operations}')

try:
    events = [
        operation_to_musical_event(beat, op) 
        for beat, op in operations.instructions
    ]
    formatter = TabFormatter()
    score = formatter.create_tab_from_events(
        mapper.map_events(events), 120, (4, 4)
    )
except:
    print("DBG:opstotabconverter")
    score = OperationsToTabConverter(operations)

print(f'2222:{formatter.format_score(score)}')

print("###################################### TEST 4 - fibonacci program compile ###################################")
program = fibonacci_program(gtrCPU)
print(f'pr0g: {program}')
formatter = TabFormatter()
print(formatter.render_program(program))
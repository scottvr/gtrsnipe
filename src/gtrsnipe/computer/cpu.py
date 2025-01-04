# computer/cpu.py

from dataclasses import dataclass
from typing import Dict, List, Optional
from ..core.operations import Operation, GuitarOperation
from ..utils.fretboard import FretboardMapper, FretPosition

@dataclass
class CPUState:
    """Represents the state of the guitar CPU"""
    accumulator: int = 0
    program_counter: int = 0
    flags: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.flags is None:
            self.flags = {
                'zero': False,
                'negative': False,
                'overflow': False
            }

class GuitarCPU:
    def __init__(self, fretboard: Optional[FretboardMapper] = None):
        self.state = CPUState()
        self.fretboard = fretboard or FretboardMapper()
        self.memory: Dict[FretPosition, int] = {}
        
    def execute(self, operation: GuitarOperation) -> None:
        """Execute a single guitar operation"""
        position = FretPosition(operation.string, operation.fret)
        
        match operation.operation:
            case Operation.LOAD:
                self.state.accumulator = self.memory.get(position, 0)
                
            case Operation.STORE:
                self.memory[position] = self.state.accumulator
                
            case Operation.ADD:
                value = self.memory.get(position, 0)
                self.state.accumulator += value
                
            case Operation.SUB:
                value = self.memory.get(position, 0)
                self.state.accumulator -= value
                
            case Operation.MUL:
                value = self.memory.get(position, 0)
                self.state.accumulator *= value
                
            case Operation.DIV:
                value = self.memory.get(position, 0)
                if value != 0:
                    self.state.accumulator //= value
                    
            case Operation.COMPARE:
                value = self.memory.get(position, 0)
                self.state.flags['zero'] = value == self.state.accumulator
                self.state.flags['negative'] = value > self.state.accumulator
                
            case Operation.JUMP:
                if operation.value:  # Conditional jump
                    if self.state.flags.get(operation.value):
                        self.state.program_counter = operation.fret
                else:  # Unconditional jump
                    self.state.program_counter = operation.fret

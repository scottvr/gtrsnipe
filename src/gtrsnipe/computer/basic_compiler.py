from typing import List, Optional
from ..core.operations import Operation, GuitarOperation
from ..utils.fretboard import FretboardMapper

class GuitarCompiler:
    def __init__(self, fretboard: Optional[FretboardMapper] = None):
        self.fretboard = fretboard or FretboardMapper()
        self.current_beat = 0.0
        
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
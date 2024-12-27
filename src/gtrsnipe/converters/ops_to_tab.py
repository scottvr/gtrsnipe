from typing import List, Optional
from ..core.operations import Operation, GuitarOperation
from ..core.tab import TabScore, TabMeasure, TabNote, FretPosition, Technique
from ..core.types import TimeSignature

class OperationsToTabConverter:
    def __init__(self, time_signature: TimeSignature = TimeSignature()):
        self.time_signature = time_signature
        
    def convert(self, operations: List[GuitarOperation]) -> TabScore:
        """Convert guitar operations to a tab score"""
        score = TabScore(time_signature=(self.time_signature.numerator, 
                                       self.time_signature.denominator))
        
        # Group operations by measure
        beats_per_measure = self.time_signature.numerator
        current_measure = []
        current_measure_num = 0
        
        for op in sorted(operations, key=lambda x: x.beat):
            measure_num = int(op.beat / beats_per_measure)
            
            # Create new measure if needed
            if measure_num > current_measure_num:
                if current_measure:
                    score.measures.append(TabMeasure(current_measure))
                current_measure = []
                current_measure_num = measure_num
            
            # Convert operation to tab note
            technique = self._operation_to_technique(op.operation)
            note = TabNote(
                position=FretPosition(op.string, op.fret),
                technique=technique,
                duration=1.0  # Default duration, could be made operation-specific
            )
            current_measure.append(note)
        
        # Add final measure
        if current_measure:
            score.measures.append(TabMeasure(current_measure))
        
        return score
    
    def _operation_to_technique(self, operation: Operation) -> Optional[Technique]:
        """Map operations to guitar techniques"""
        technique_map = {
            Operation.ADD: Technique.HAMMER,
            Operation.SUB: Technique.PULL,
            Operation.MUL: Technique.BEND,
            Operation.DIV: Technique.SLIDE,
            Operation.COMPARE: Technique.HARMONIC,
            Operation.LOAD: Technique.TAP,
            Operation.STORE: Technique.PICK
        }
        return technique_map.get(operation)
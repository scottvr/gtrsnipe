from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from ..core.operations import Operation, GuitarOperation
from ..core.types import TimeSignature, MusicalEvent
from .cpu import GuitarCPU, CPUState

@dataclass
class TimedInstruction:
    """Represents an instruction with its execution timing"""
    operation: GuitarOperation
    start_cycle: int
    end_cycle: int
    
    @property
    def cycles(self) -> int:
        return self.end_cycle - self.start_cycle

class GuitarProgram:
    def __init__(self, cpu: GuitarCPU, time_signature=(4, 4), tempo=120):
        self.cpu = cpu
        self.time_signature = time_signature
        self.tempo = tempo
        self.cycles_per_beat = 4
        self.instructions: List[Tuple[int, GuitarOperation]] = []
        self.cycle_times: Dict[Operation, int] = {
            Operation.LOAD: 1,
            Operation.STORE: 1,
            Operation.ADD: 2,    # Hammer-ons take 2 cycles
            Operation.SUB: 2,    # Pull-offs take 2 cycles
            Operation.MUL: 3,    # Bends take 3 cycles
            Operation.DIV: 2,    # Slides take 2 cycles
            Operation.COMPARE: 1,
            Operation.JUMP: 1
        }
    
    def add_instruction(self, beat: float, operation: GuitarOperation):
        """Add an instruction to be executed at a specific beat"""
        self.instructions.append((beat, operation))
    
    def compile(self, execute: bool = True) -> List[TimedInstruction]:
        """
        Compile program into timed instructions.
        
        Args:
            execute: If True, actually execute instructions on CPU
        """
        timed_instructions = []
        cycle_usage = {}  # Track when each string is available
        
        # Sort instructions by beat time
        sorted_instructions = sorted(self.instructions, key=lambda x: x[0])
        
        for beat, operation in sorted_instructions:
            # Calculate start cycle
            start_cycle = int(beat * self.cycles_per_beat)
            
            # Check if string is busy
            string_busy_until = cycle_usage.get(operation.string, 0)
            if start_cycle < string_busy_until:
                start_cycle = string_busy_until
            
            # Calculate operation duration
            operation_cycles = self.cycle_times.get(operation.operation, 1)
            
            # If operation is a slide, calculate based on distance
            if operation.operation == Operation.DIV and operation.value:
                operation_cycles = 1 + abs(operation.fret - operation.value) // 3
            
            end_cycle = start_cycle + operation_cycles
            
            # Execute on CPU if requested
            if execute:
                self.cpu.execute(operation)
            
            # Mark string as busy until operation completes
            cycle_usage[operation.string] = end_cycle
            
            # Add to timed instructions
            timed_instructions.append(TimedInstruction(
                operation=operation,
                start_cycle=start_cycle,
                end_cycle=end_cycle
            ))
        
        return timed_instructions
    
    def get_current_state(self) -> CPUState:
        """Get current CPU state"""
        return self.cpu.state
    
    def reset(self):
        """Reset program and CPU state"""
        self.cpu.state = CPUState()
        self.instructions.clear()

def create_musical_events(program: GuitarProgram, timed_instructions: List[TimedInstruction]) -> List[MusicalEvent]:
    """Convert compiled program to musical events for tab generation"""
    events = []
    
    for inst in timed_instructions:
        # Convert cycles to actual time
        seconds_per_cycle = 60.0 / (program.tempo * program.cycles_per_beat)
        start_time = inst.start_cycle * seconds_per_cycle
        duration = inst.cycles * seconds_per_cycle
        
        # Create musical event
        events.append(MusicalEvent(
            time=start_time,
            duration=duration,
            pitch=0,  # We'll need proper pitch mapping
            velocity=80 if inst.operation.operation in [Operation.ADD, Operation.MUL] else 60,
            string=inst.operation.string,
            fret=inst.operation.fret,
            technique=_operation_to_technique(inst.operation.operation)
        ))
    
    return events

def _operation_to_technique(operation: Operation) -> Optional[str]:
    """Map operations to guitar techniques"""
    technique_map = {
        Operation.ADD: "hammer-on",
        Operation.SUB: "pull-off",
        Operation.MUL: "bend",
        Operation.DIV: "slide",
        Operation.LOAD: "tap",
        Operation.STORE: "pick"
    }
    return technique_map.get(operation)

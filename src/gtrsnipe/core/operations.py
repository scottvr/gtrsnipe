from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any

class Operation(Enum):
    LOAD = "load"
    STORE = "store"
    ADD = "add"
    SUB = "subtract"
    MUL = "multiply"
    DIV = "divide"
    MOD = "modulo"
    COMPARE = "compare"
    JUMP = "jump"
    RETURN = "return"

@dataclass
class GuitarOperation:
    operation: Operation
    fret: int
    string: int
    technique: Optional[str] = None
    value: Optional[Any] = None
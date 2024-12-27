from gtrsnipe import MidiToTabConverter, TimeSignature, FretPosition, Technique, TabFormatter, GuitarPositionMapper, GuitarCPU, GuitarProgram, ASTToGuitarCompiler
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
    program = compiler.compile_function(func)
    print(f'pr: {dir(program)}') 
    print(f'pr: {program.instructions}') 
    # Compile to timed instructions
    timed_instructions = program.compile(execute=True)
    print(f'ti: {dir(timed_instructions)}') 
    print(f'ti: {timed_instructions}') 
    
    # Convert to musical events
    events = create_musical_events(program, timed_instructions)
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


# Test with fibonacci
def test_fibonacci():
    def fib(n):
        if n <= 1:
            return n
        a, b = 0, 1
        for i in range(2, n):
            a, b = b, a + b
        return b
    
    return(compile_and_run(fib))

if __name__ == "__main__":
    # Test with our Mary had a little lamb MIDI
    #print(test_conversion("input.mid"))
    print(compile_and_run(fizzbuzz))
    #print(test_fibonacci())
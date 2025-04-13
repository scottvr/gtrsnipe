# gtrsnipe (pronounced "guttersnipe")

This codebase is uttterly ridiculous.. normally my stuff is firmly in the *ludicrous* zone; I'm not sure how I veered so far into *ridiculous* territory aside from that I got nerdsniped by an [impossible claim by someone on hackernews](https://news.ycombinator.com/item?id=42294766) that [guitar tab was turing complete](https://github.com/tehruhn/turing_complete_guitar). (storing to memory seems an obvious obstacle but..) 

I wanted to see what I might come up with, a different machine, perhaps involving a looper pedal blah blah blah.. it's been a few weeks and I forget what all ridiculous iterations it went through.  First I converted [his mm:ss-based time implementation]() with tempo and time signature, then added alternate tunings, then it was off to the races, without any finish line. 

In the process though.. I ended up with ast to tablature, midi to guitar tab (with an optimal fretboard mapper that's kinda cool. maybe deserves finishing and packaging), guitar tab formatter, a "guitputer" machine of sorts and a couple of attempts at a "compiler" for it.. 

Some of those things I just mentioned are useful things, and someone may find some of this code useful, or interesting, or funny.

Up until about the halfway point of the sniping's duration, I had kept a journal (below) planning to document this. Yeah, I probably won't. :-)
Code in [the guttersnipe repo](https://github.com/scottvr/gtrsnipe) also includes half-finished test scripts and redirected output txt files for debugging. Enjoy.

-----

## Initial Infrastructure

- Changed timing notation from mm:ss to measure.beat format
- Added configurable time signature support
- basic instruction set for guitar operations

## Memory & Addressing

- fret-based memory addressing system
- capo support as base address register
- alternate tunings as memory access patterns
- using string selection as memory banks

## Instruction Set Architecture

- a Turing Machine ISA including the operations
   - LOAD
   - STORE
   - ADD
   - SUB
   - MUL
   - DIV
   - CMP
   - JMP
- Expanded instruction set with guitar techniques (hammer-ons, pull-offs, slides, etc.)
- Added timing specifications for each instruction type
- Created cycle count system for different operations

## CPU & Compilation

- Developed GuitarCPU class
- Created program compiler for converting operations to tab, demo with python Fibonacci function, which is converted to Operations via parsing the AST, then out to tab (or mid, or abc, or ???)
- Can output to midi. And just for grins, can convert midi to opcodes, for ridiculous code that sounds good, and any other input/ouput combination/direction involving midi (file), GuitarCPU ISA, ABC notation, and guitar tablature notation. 
- Implemented basic instruction scheduling

## Tab Generation & Output

- Created TabFormatter for proper guitar tablature output
- Added measure bars and timing markers
- Implemented proper string representation
- (original implementation was just lists of 5th (power) chords, and not actually in tab notation

## Performance Validation & Optimization

- Added FretboardMapper to track valid playing positions
- Created TechniqueRestrictions to validate playability
- Implemented position optimization to avoid impossible techniques
- Developed system to remap unplayable positions to equivalent playable ones
- Added intelligent scoring for optimal position selection

## Optimization Refinements

- Enhanced position remapping to preserve musical intent
- Improved handling of technique-specific restrictions
- Added context-aware position selection (considering previous positions)
- Removed ambiguous notation (like zero-padding fret numbers)
- Implemented clean tab output without remapping markers

## Compiler System

- Created GuitarCompiler class for higher-level translation
- Added operation to instruction mapping
- Implemented memory management system
- Created instruction timing analyzer
- Added support for operation sequences and control flow

## additional Enhancements

- Improved cycle-accurate timing representation
- Added proper handling of technique duration
- Enhanced position optimization for complex sequences
- Refined tab output for maximum readability and playability

## went off the deep end of time waste

### Among the useful things are:
- a MIDI to Guitar Tab converter
- a FretboardMapper, which can be used to influence decisions made when choosing a fret position for the next incoming note from a midi file being read
- an ABC to MIDI class
- the inverse capability from the above two items,
- an ascii tab renderer
- more

### mostly useless but potentially interesting are:
- a virtual ("guitar") CPU
- a compiler for it
- another compiler for it
-  code writen in Python can be transpiled to a guitarcpu program, which consists of a series of note events (fret positions and fretting techniques), presented linearly at a tempo which can then be
    - output as guitar tab
    - output as a midi file
- music encoded in a MIDI file can be converted to
  - guitar tab
  - a series of musical events whcih can be mapped to GuitarCPU operations.
    - why would anybody want this?
      these capabilities mean that one can
        - take working python code and see what it sounds like
            - played on guitar from reading tab
            - as a midi file
        - take a song as midi data or guitar tab
            - convert it to whichever it is not
            - including GuitarCPU program instruction listing
            - and by extension, python code if you wish
  - a few different takes and incomplete versions of some of the aforementioned stuff


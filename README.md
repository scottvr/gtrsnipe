# gtrsnipe (pronounced "guttersnipe")

Ridiculous.. I got nerdsniped by an impossible claim by someone on hackernews that guitar tab was turing complete. (storing to memory seems an obvious obstacle but..) 
I wanted to see what I might come up with, a different machine, perhaps involving a looper pedal blah blah blah.. it's been a few weeks and I forget what all ridiculous iterations it went through.  First I converted his second-based time implementation with tempo and time signature, then added alternate tunings, the. it was off to the races, without any finish line. 

In the process though.. I ended up with ast to tablature, midi to guitar tab (with an optimal fretboard mapper that's kinda cool. maybe deserves finishing and packaging), guitar tab formatter, a "guitputer" machine of sorts and a couple of attempts at a "compiler" for it.. 

Some of those things I just mentioned are useful things that I don't know if they already exist, but someone may find some of this code useful, or interesting, or funny.

Up until about the halfway point, I had kept a journal (below) planning to document this. Yeah, I probably won't. :-)
Code in the repo includes half-finished test scripts and redirected output txt files for debugging. Enjoy.

=============================

Initial Infrastructure

Changed timing notation from mm:ss to measure.beat format
Added configurable time signature support
Created basic instruction set for guitar operations

Memory & Addressing

Implemented fret-based memory addressing system
Added capo support as base address register
Explored alternate tunings as memory access patterns
Developed concept of using string selection as memory banks

Instruction Set Architecture

Expanded instruction set with guitar techniques (hammer-ons, pull-offs, slides, etc.)
Added timing specifications for each instruction type
Created cycle count system for different operations

CPU & Compilation

Developed GuitarCPU class
Created program compiler for converting operations to tab
Implemented basic instruction scheduling

Tab Generation & Output

Created TabFormatter for proper guitar tablature output
Added measure bars and timing markers
Implemented proper string representation

Performance Validation & Optimization

Added FretboardMapper to track valid playing positions
Created TechniqueRestrictions to validate playability
Implemented position optimization to avoid impossible techniques
Developed system to remap unplayable positions to equivalent playable ones
Added intelligent scoring for optimal position selection

Optimization Refinements

Enhanced position remapping to preserve musical intent
Improved handling of technique-specific restrictions
Added context-aware position selection (considering previous positions)
Removed ambiguous notation (like zero-padding fret numbers)
Implemented clean tab output without remapping markers

Compiler System Development

Created GuitarCompiler class for higher-level translation
Added operation to instruction mapping
Implemented memory management system
Created instruction timing analyzer
Added support for operation sequences and control flow

Final Enhancements

Improved cycle-accurate timing representation
Added proper handling of technique duration
Enhanced position optimization for complex sequences
Refined tab output for maximum readability and playability

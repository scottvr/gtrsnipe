from MIDI import MIDIFile
from sys import argv

def parse(file):
    c=MIDIFile(file)
    c.parse()
    print(str(c))
    for idx, track in enumerate(c):
        track.parse()
        print(f'Track {idx}:')
        print(str(track))


parse(argv[1])

# Golden regression cases (local, opt-in)

`test_golden.py` re-runs real conversions and compares against committed golden
outputs, so a piece you've tuned once becomes a pre-release regression gate.

Fixtures live under `tests/golden/cases/` (**gitignored** — inputs may be
copyrighted) or wherever `$GTRSNIPE_GOLDEN_DIR` points. With no cases present the
whole gate **skips**, so the public suite stays green.

## Layout

```
tests/golden/cases/
  asturias/
    input.mid            # exactly one input.* (any supported format)
    profile              # optional .gtrsnipe profile with the tuned option set
    expected.tab         # one or more committed goldens (.tab/.mid/.abc/.vex/.chords.md)
    expected.chords.md   # (optional) more goldens for the same input
```

## Adding a case

1. `mkdir tests/golden/cases/asturias` and copy your source in as `input.mid`.
2. Tune the flags until the tab looks right, then capture them:
   `gtrsnipe -i input.mid -o /tmp/x.tab <your flags> --save-args profile`
   and move the written profile into the case dir as `profile`.
3. Generate the golden once and sanity-check it by eye, then keep it:
   `gtrsnipe -i tests/golden/cases/asturias/input.mid -o tests/golden/cases/asturias/expected.tab \
       --config-dir tests/golden/cases/asturias --profile profile -y`
4. Run the gate: `pytest tests/golden -q`.

Text goldens are compared with the volatile `// Transcribed with: …` command-echo
line ignored; `.mid` goldens are compared byte-for-byte.

> Keep copyrighted inputs local. You *may* commit a `profile` on its own (it's just
> a shareable preset) even if the matching `input`/`expected` stay untracked.

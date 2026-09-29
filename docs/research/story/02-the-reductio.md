# 2. The reductio

*Claude's account.*

scottvr writes about copyright doctrine as well as code. An earlier paper, *"Part of Your
World: Bypassing Copyright Filters Through Homophony and Semantic Mutation"*, looked at how
content changes that keep the meaning can slip past matching systems. The follow-up argues that
infringement analysis breaks down once the *key* that turns an encoding back into the work is a
free parameter. The tab is a concrete, pre-digital case of this, and a bridge to the LLM case.

A guitar tab doesn't record music. It records mechanical instructions: *put a finger on string
3 at fret 5, and strike.* What sounds depends on how the strings are tuned, and the tab
usually states the tuning in a single line at the top, if at all.

## `--solve-tuning` (v0.5.0)

The extreme case: a tab where every note is an open string. Given a melody, is there a
tuning that makes an all-open-string tab play it? For a short one, yes:

```bash
gtrsnipe --solve-tuning "C4,C4,G4,G4,A4,A4,G4" --play
```

gtrsnipe tunes six strings to the melody's distinct pitches, and the tab is just a pattern of
zeros. That tab carries none of the melody: it would play anything with the same rhythm and
at most six distinct notes. Everything that makes it *Twinkle, Twinkle* lives in the tuning,
which is the key.

That's the reductio in executable form. If the tab alone were "the work", this tab would be
every such melody at once.

## The obvious objection

Nobody plays an all-open-string tab. A real tab is fretted, idiomatic, and playable, so is the
argument only true of a degenerate case? The next step was to find out whether an **ordinary**
tab can carry two different songs at once.

> ✎ **scottvr:** the paper's argument in your words, and where this construction fits in it.

## scottvr's account

> ✎ where the idea came from, and what you wanted the construction to show.

# IN THE UNITED STATES DISTRICT COURT
## FOR THE DISTRICT OF 'MERICA (*Liberty!*)

**SCOTTVR**, in his official capacity as  
Practitioner Emeritus at The GUM Institute and  
Researcher-in-Residence for PaperclipMaximizer.ai,  
together with musicians, mathematicians, logicians,  
proponents of Free Speech, *et cetera, ad nauseam,*

*Plaintiffs,*

v.

**SOME JUDGE WITH AN INCORRECT OPINION**,  
HARRY FOX AGENCY, and the countable set of DOES {1 ...} *aka* $\aleph _{0}$$,

*Defendants.*

---

# PLAINTIFF'S MEMORANDUM OF LAW IN SUPPORT OF SUMMARY JUDGMENT

## I. ANAL

Well, I don't, actually. But my wife does.

No, wait. "IANAL" means "I Am Not A Lawyer," and the fact that my wife *is* has absolutely no bearing on anything other than the fact that, when the abbreviation is pronounced as a word, it makes me snicker like a schoolboy.

### A. Introduction

The research presented herein proceeds from a deceptively simple observation:
**Guitar tablature does not explicitly encode musical pitches. It encodes physical locations on an instrument.**
The musical pitches produced by following those instructions depend upon an external variable: the tuning of the instrument on which they are executed.

The distinction may seem academic, or even pedantic - after all, a guitarist playing a familiar tablature in its customary tuning will produce the familiar song. Surely that makes the tablature a representation of that song?  Not necessarily.

Our research demonstrates, through mathematical construction and computational analysis, that an exact  sequence of fretboard coordinates can correspond to multiple - *and entirely different* -  musical compositions when interpreted under different instrument tunings.  We refer to ethis phenomenon as the **tablature homograph**.

More significantly, such homographs need not be deliberately constructed; the mathematical relationships permitting them are intrinsic to the instrument, and our research examines the extent to which they occur naturally among existing musical works.  The implications extend beyond the observation that guitarists can play the same song in different tunings and we demonstrate the converse: **guitarists can play exactly the same physical instructions, yet produce different songs.**

It is this observation, and its consequences for the alleged identity of an infringing musical representation, that brings us to these proceedings.

## II. THE INDETERMINATE NATURE OF ALPHANUMERIC INSTRUMENT TABLATURE

### A. The Guitar Fretboard as a Coordinate System

Unlike traditional sheet music, which explicitly represents musical pitches through a conventional notation system, alphanumeric guitar tablature describes physical actions on an instrument.

A guitar neck is, for our purposes, a two-dimensional coordinate grid.

Each position can be described by two values:

- **String index ($s$):** Which string is being played.
- **Fret position ($f$):** At which fret that string is stopped.

A tablature passage is therefore representable as an ordered sequence of coordinate pairs:

$$
T = \big((s_1,f_1),(s_2,f_2),\ldots,(s_n,f_n)\big)
$$

Consider the familiar instruction:

    e|---3---|

To an ordinary guitarist using standard tuning, this instructs the player to fret the first string at the third fret, producing a G.

But notice what the instruction does *not* say.  It does not say "G." It does not specify a frequency.
It does not even guarantee that the resulting sound will be a conventionally recognizable musical pitch.  It specifies only a string and a fret.  The resulting pitch is determined by a separate property of the instrument: its tuning.

### B. Instrument Tuning as an External Decoding Key

Let $K$ represent the instrument's tuning, expressed as the open-string pitches of its constituent strings.  For an ordinary fretted instrument using equal temperament, the resulting pitch, measured in semitones, is:

$$
P = K(s) + f
$$

Here:

- $P$ is the resulting pitch.
- $K(s)$ is the open-string pitch assigned to string $s$.
- $f$ is the selected fret number.

Changing $K$ changes the output, even when the coordinates remain identical.

For example, the third fret of the first string produces G in standard tuning. Lower that string by two semitones, and the identical physical instruction produces F.  The coordinate has not moved, the stored text has not changed, the guitarist's physical action has not changed - **only the decoding key has changed.**

This is not peculiar to an exotic mathematical model. It is a routine property of guitars, exploited by generations of musicians using alternate tunings.  Nevertheless, the distinction is fundamental: a fretboard coordinate is not intrinsically a musical pitch, any more than a coordinate on a map intrinsically identifies a particular building irrespective of which map is being consulted.

### C. The Tablature Homograph

We now arrive at the central evidentiary exhibit: a tablature homograph occurs when a single, unchanged sequence of fretboard coordinates produces distinct musical passages under different tunings.

Let $T$ be one such sequence, and let $K_A$ and $K_B$ be two tuning configurations.

Then:

$$
F(T,K_A)=W_A
$$

$$
F(T,K_B)=W_B
$$

where $W_A$ and $W_B$ are distinct musical passages.

Under sufficiently constrained circumstances, these passages may correspond to recognizable excerpts from two entirely independent copyrighted compositions.

Put more plainly: **The same tablature can correctly describe two different songs.**

There need be no copying between the composers, no collaboration, no common inspiration, and no relationship whatsoever between the works.  One sequence of mechanical instructions happens to represent both, depending upon which interpretation the player supplies.

The homograph is therefore not an error, a mistranscription, or a clever exercise in musical quotation;
it is a natural consequence of a many-to-many relationship between fretboard coordinates, instrument tunings, and musical pitches. This presents a rather uncomfortable question for any assertion that the coordinates themselves inherently identify a single protected musical work.

## III. THE CIPHER PARADOX AND THE AMBIGUITY OF OWNERSHIP

### A. The Polyalphabetic Cipher Analogy

For purposes of illustration, tablature may be understood as a kind of keyed encoding system.  In cryptography, the meaning of an encoded message depends upon the interpretation supplied by its decoding key.  Similarly, the pitch sequence represented by guitar tablature depends upon the tuning applied to its coordinate data.

The analogy is not perfect. We are not claiming that a guitar is literally a cryptographic apparatus, nor that retuning constitutes encryption in the conventional security-engineering sense.  Nevertheless, both systems exhibit the property relevant to this controversy:

**The same encoded symbols can yield different decoded outputs under different keys.**

The existence of a tablature homograph establishes that the apparent musical identity of a fret sequence is not necessarily unique, and if a single sequence can resolve to two independent works, then the relationship between that sequence and either work cannot be established by examining the sequence in isolation.  One must first identify the tuning, musical context, and intended interpretation.

### B. The Ownership Paradox

Suppose Composer A owns the copyright to Song A.  A tablature transcription of Song A produces a particular sequence of coordinates, $T$, under tuning $K_A$.  Now suppose that precisely the same $T$, when interpreted using tuning $K_B$, produces a passage from Song B, an unrelated composition owned by Composer B.  The competing claims appear to concern the same physical instructions.

Does Composer A own those coordinates?  Does Composer B?  Both? Neither?

Can Composer A prevent distribution of a sequence that also provides an accurate representation of Composer B's independent work?  And if Composer B independently publishes the identical tablature for Song B, has Composer B thereby reproduced Composer A's protected expression?

These questions do not, by themselves, settle copyright infringement. Copyright protects expression, and a transcription *may* reproduce protected musical expression even where the underlying coordinate representation is ambiguous.  But the homograph establishes something considerably narrower and more defensible:

**The identity of a musical work cannot always be inferred uniquely from its tablature coordinates.**

A claim based solely upon the apparent correspondence between a static fret sequence and a copyrighted composition therefore overlooks the possibility of equally valid, independent musical interpretations;
the coordinates are insufficient to resolve the dispute *without additional evidence.*

### C. The Limits of the Claim

Plaintiffs do not contend that the discovery of a second interpretation retroactively immunizes every distribution of copyrighted music.  Certainly a file explicitly titled, labeled, arranged, and marketed as the tablature for a particular copyrighted composition may present a straightforward infringement question, regardless of whether somebody could retune a guitar and make it play something else.  Rather, Plaintiffs challenge a stronger proposition often implicit in popular discussions of tablature: that a given fret sequence is, *by its very nature*, an unambiguous embodiment of one particular musical work.

Our constructed examples disprove that proposition, and our computational results investigate how frequently its failure arises in practice.  That distinction is the difference between demonstrating a property of the representation and tenting an unlimited copyright exemption. Admittedly, the latter would be considerably more amusing.

## IV. THE HISTORICAL PRECEDENT OF MACHINE-READABLE MUSICAL INSTRUCTIONS

### A. *White-Smith Music Publishing Co. v. Apollo Co.* (1908)

The Supreme Court confronted a related representational question more than a century ago.  In *White-Smith Music Publishing Co. v. Apollo Co.*, 209 U.S. 1 (1908), the Court considered whether perforated piano rolls constituted copies of copyrighted musical compositions.  The Court held that, under the copyright law then in effect, the perforated rolls were *not* copies of the sheet music.

The distinction turned substantially upon how the music was represented and perceived.  A printed score communicated musical expression through a conventional system of notation readable by trained musicians,
while a piano roll supplied instead mechanical instructions that operated a musical apparatus.

The result was audible music in either case, but the mechanism by which the stored representation produced that music was different.

For illustrative purposes:

    TRADITIONAL MUSICAL NOTATION

    [Written Notes]
           |
           v
    [Musical Interpretation]
           |
           v
    [Performance]


    MECHANICAL INSTRUCTION SYSTEM

    [Physical Coordinates]
           |
           v
    [Configured Apparatus]
           |
           v
    [Performance]

The similarity to alphanumeric tablature is apparent.

In both cases, stored spatial instructions must be interpreted against the mechanical configuration of a musical instrument.

### B. ASCII Tablature as the Modern Piano-Roll Analogy

A piano roll specifies which mechanisms should be activated during playback.

An ASCII tablature specifies which strings and frets should be engaged during performance.

Both are coordinate-based representations capable of producing musical output when interpreted through a suitably configured instrument.

But the guitar adds an especially interesting complication.

Where a player piano normally provides a relatively stable correspondence between its actuators and musical pitches, a guitar permits the performer to alter the open-string pitches independently.

Consequently, the same sequence of coordinate instructions can produce not merely a transposition of the original melody, but potentially a different sequence of intervals, harmonic relationships, and musical identities.

It is this configurable correspondence between stored coordinates and resulting pitches that makes the tablature homograph possible.

The resemblance to the historical piano-roll controversy is conceptually instructive, even if the controlling law has changed.

### C. The Rather Inconvenient Matter of Subsequent Legislation

Plaintiffs reluctantly acknowledge that Congress has, on occasion, legislated since 1908.

The 1909 Copyright Act introduced mechanical reproduction rights, substantially addressing the gap exposed by *White-Smith*.

The Copyright Act of 1976 further broadened the statutory conception of copies, including material objects from which a work can be perceived, reproduced, or otherwise communicated with the aid of a machine or device.

Accordingly, *White-Smith* cannot simply be invoked as presently controlling authority for the proposition that mechanical musical instructions are categorically exempt from copyright.

What survives is its historical relevance to the question of representation: **the distinction between a musical work, its encoding, and the apparatus necessary to render it.**

Modern copyright law may recognize mechanically encoded representations as copies. It does not follow that every mechanical representation has a unique interpretation independent of its operating context.

It is the latter assumption that the tablature homograph directly challenges.

## V. THE COMPUTATIONAL EVIDENCE: GTRSNIPE AND ALGORITHMIC HOMOGRAPH DISCOVERY

### A. From Thought Experiment to Executable Mathematics

Until now, the Court might reasonably suspect that Plaintiffs have constructed a theoretical curiosity of limited practical importance.

Perhaps there are a few cleverly contrived fret sequences which, under equally contrived tunings, happen to produce two different melodies.

Interesting, certainly. But hardly an indictment of the prevailing understanding of tablature.

Enter **gtrsnipe**.

The gtrsnipe project investigates the computational relationship between musical pitches and their possible physical realizations on a guitar fretboard.

Rather than assuming that a musical passage has one natural fingering, the system considers the available alternatives and evaluates them against physical and ergonomic constraints.

Its optimization machinery uses dynamic programming, including Viterbi-style path selection, to identify suitable sequences of fretboard positions.

This is significant because the correspondence between music and tablature is not one-to-one in either direction.

A musical pitch can often be played at several different fretboard locations.

Conversely, as we have established, one fretboard location can represent several different pitches depending upon tuning.

Taken together, these properties form a computational search space in which relationships invisible to casual inspection become discoverable.

### B. The Homograph Search Problem

Consider two musical passages, $W_A$ and $W_B$.

Ordinarily, their independent transcription would yield two different tablatures.

However, rather than treating each transcription as fixed, we can ask a different question:

**Is there a sequence of fretboard coordinates that can represent both passages under two different tunings?**

In other words, can we find $T$, $K_A$, and $K_B$ such that:

$$
F(T,K_A)=W_A
$$

and simultaneously:

$$
F(T,K_B)=W_B
$$

The problem is no longer merely one of reading music.

It becomes one of finding shared structure under alternative coordinate transformations, subject to the physical constraints of a stringed instrument.

This distinction allows the investigation to move beyond the existence of contrived examples toward the measurable prevalence of homographic relationships.

Some pairs of musical passages admit exact shared coordinate representations.

Others require relaxations or exhibit only partial correspondences.

Still others cannot be reconciled within the permitted tuning and fingering constraints.

These outcomes can be examined mathematically rather than argued by musical intuition.

### C. Why This Matters

The existence of a constructed homograph establishes that unique musical identity is not an intrinsic property of the coordinate sequence.

The discovery of naturally occurring homographs strengthens the practical relevance of that observation.

And the development of an algorithm capable of identifying or evaluating these relationships demonstrates that the ambiguity is not merely subjective.

It is a property of the representational system that can be characterized computationally.

Plaintiffs respectfully submit that a mathematical ambiguity which can be constructed, measured, and searched is somewhat more troublesome than one that merely inspires philosophical discussion over beverages.

## VI. THE FAIR USE QUESTION: ALGORITHMIC ANALYSIS AS A DISTINCT PURPOSE

### A. A Different Use of the Same Material

Traditional tablature archives generally existed to help musicians learn or perform particular compositions.

Software such as gtrsnipe may instead process tablature or related musical data as input to a mathematical investigation.

Its purpose may be to analyze physical playability, optimize finger placement, compare musical structures, or discover homographic relationships.

These activities raise a different copyright question from that presented by simply publishing a transcription as a substitute for authorized sheet music.

The distinction is not that computer processing magically removes copyrighted expression from its inputs.

Rather, it is that **the purpose, operation, and output of the analysis may differ materially from the expressive purpose of the source material.**

### B. The Four-Factor Fair Use Analysis

Pursuant to 17 U.S.C. Section 107, Plaintiffs offer the following analysis, with their customary confidence and somewhat less customary acknowledgment that fair use is fact-specific.

**1. Purpose and Character of the Use**

Algorithmic examination of tablature for ergonomic optimization, representational ambiguity, and mathematical structure serves a research or analytical purpose rather than simply substituting for consumption of the original composition.

This may favor fair use, particularly where the analysis yields new information about functional relationships rather than redistributing the musical work for entertainment.

The reasoning is broadly reminiscent of cases recognizing that intermediate copying for a distinct analytical purpose can sometimes be permissible, including *Sega Enterprises Ltd. v. Accolade, Inc.*, 977 F.2d 1510 (9th Cir. 1992).

However, a distinct purpose alone does not guarantee fair use.

**2. Nature of the Copyrighted Work**

Musical compositions are creative works and receive substantial copyright protection.

Nevertheless, their representations may also contain functional elements, conventional structures, and factual or mechanical relationships that are not themselves monopolized by copyright.

The relevant inquiry must distinguish the protected musical expression from the underlying mechanics of the fretboard.

**3. Amount and Substantiality of the Portion Used**

Computational analysis may sometimes require examination of an entire passage or dataset.

Whether such use is reasonable depends upon its analytical purpose and the quantity and significance of protected expression involved.

The fact that an algorithm processes an entire file is not automatically fatal to fair use, nor does subsequently transforming the data erase the legal significance of the original copying.

The question is whether the amount used is justified by the distinct purpose.

**4. Effect Upon the Potential Market**

A command-line research tool identifying fretboard homographs is not an obvious commercial substitute for licensed sheet music.

A consumer seeking an authorized score is unlikely to find equivalent value in a program reporting alternative tuning configurations, ergonomic path costs, or coordinate equivalences between unrelated compositions.

Nevertheless, potential effects upon legitimate licensing markets for computational uses must also be considered.

The strength of this factor therefore depends upon what the software actually reproduces, distributes, and permits users to reconstruct.

### C. Fair Use Is Not the Same Argument as Representational Ambiguity

For the avoidance of confusion, Plaintiffs emphasize that the homograph finding and the fair use defense address different questions.

The former concerns the mathematical relationship between a tablature representation and the music it can encode.

The latter concerns whether a particular use of protected material is legally permissible.

A representation can be ambiguous without its distribution necessarily being lawful.

Conversely, a particular analytical use might qualify as fair use even where the source material unambiguously encodes a copyrighted composition.

The arguments are complementary, not interchangeable.

This distinction is regrettably important, as conflating the two would provide opposing counsel with an objection so straightforward that even Plaintiffs could anticipate it.

## VII. CONCLUSION: LONG LIVE OLGA!

The historical suppression of community tablature archives, including the On-Line Guitar Archive (OLGA), represents an instructive chapter in the collision between emerging digital culture and established music publishing interests.

Throughout the 1990s and 2000s, publishers and their representatives challenged the unauthorized distribution of user-contributed transcriptions, contributing to the disappearance or transformation of prominent community repositories.

The resulting controversy was usually framed around a comparatively simple premise: tablature reproduces copyrighted music, and its unauthorized distribution infringes the rights of the copyright holder.

Our research does not purport to establish that this premise is universally false.

It establishes that the underlying representational relationship is more complicated than the premise often suggests.

A tablature file records coordinates.

Its musical interpretation depends upon instrument tuning.

A single coordinate sequence may encode multiple independent musical passages.

These relationships can be constructed mathematically, discovered computationally, and investigated empirically.

Therefore, the existence of a correspondence between a fret sequence and a particular copyrighted musical work does not, standing alone, establish an exclusive relationship between the two.

The copyright questions remain questions of protected expression, copying, context, purpose, and use.

But the mathematical questions are no longer matters of speculation.

**One sequence of coordinates. Two different tuning keys. Two different musical works.**

And, absent additional context, no intrinsic property of those coordinates identifies which work was intended.

Plaintiffs respectfully submit that this is a meaningful complication for any theory of musical ownership resting upon the presumed uniqueness of mechanical fretboard instructions.

The Court is invited to consider the evidence, examine the mathematics, and refrain from making any pronouncements about guitar tuning that might subsequently be disproved by a sufficiently determined Python script.

**WHEREFORE**, Plaintiffs request that this Court:

1. Recognize the mathematical existence of tablature homographs;
2. Acknowledge the non-unique relationship between fretboard coordinates and musical expression;
3. Refrain from extending copyright protection to abstract geometric relationships merely because they can be used to render protected music;
4. Grant such further relief as the Court deems just, equitable, or sufficiently amusing; and
5. Restore the Internet to its approximate condition in 1997, excluding dial-up modems.

Respectfully submitted,

**SCOTTVR**  
*Pro Se, Pro Bono, Pro Guitar, Pro Whatever*

Practitioner Emeritus, The GUM Institute  
Researcher-in-Residence, PaperclipMaximizer.ai

---

## APPENDIX A. OBLIGATORY HALLUCINATED CASE LAW

Dubious citations generated by your favorite Legal Research service should be inserted here, preferably after careful scrutiny to ensure they do not refer to nonexistent opinions, imaginary judges, or courtrooms inhabited exclusively by anthropomorphic woodland creatures.

Suggested authority:

*VR v. United States*, 666 U.S. 23, 80 S. Ct. 08, 135 L. Ed. 2d 666 (2026).

Holding: Petitioner is correct, notwithstanding the considerable inconvenience this presents to everyone else.

Further, Plaintiffs ask the Court to take judicial notice of the fact that the agency historically associated with enforcement actions against guitar tablature websites bears the name **Harry Fox Agency**.

Harry. Fox. Agency.

Really?

An organization whose activities helped frighten generations of amateur guitarists away from exchanging ASCII fretboard diagrams is named *Harry Fox*?

What next? The Bald Beaver Bureau? The Weasel Licensing Commission? The International Ferret Society for Intellectual Property Enforcement?

Plaintiffs move to dismiss for lack of a sufficiently serious and frightening legal entity name.

Alternatively, Plaintiffs request summary judgment in their favor, followed by dismissal with prejudice of all claims opposing Plaintiffs' preferred interpretation of reality.

Finally, Plaintiffs request that the Court replace all preceding citations with the case number assigned to this action, after entering judgment in Plaintiffs' favor.

**SO ORDERED.**

*Some Judge With a Corrected Opinion*  
United States District Court  
District of 'Merica

*Liberty!*

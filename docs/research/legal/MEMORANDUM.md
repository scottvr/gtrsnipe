# LEGAL RESEARCH MEMORANDUM

## Decoder-Dependent Guitar Tablature, Representational Ambiguity, and Copyright Infringement

**Project:** [gtrsnipe](https://github.com/scottvr/gtrsnipe)  
**Status:** Working technical and legal analysis; research in progress  
**Jurisdiction:** United States federal copyright law  
**Date:** October 2026

> **Scope.** This memorandum identifies a mathematically demonstrable ambiguity in guitar tablature, presents the project's reported experimental findings, and examines questions that ambiguity may raise in copyright disputes. It does **not** contend that every tablature file is uncopyrightable, that a homograph automatically defeats an infringement claim, or that all computational processing of copyrighted music is fair use. It is not a legal opinion addressing any particular dispute.
>
> **Evidence status.** The R03-R05 figures below are transcribed from the project's research summary. Their authoritative methods, samples, qualifications, and revisions belong in the evolving [experimental results](../results/). The individual report filenames and their current contents should be verified and linked directly before this memorandum is cited as evidence in litigation.

## Questions Presented

1. Can a fixed sequence of guitar string-and-fret coordinates represent more than one musical passage, even when performed on physically realizable instruments?
2. If so, what can the identity of two such sequences establish about copying of a particular musical composition, especially in an unkeyed short excerpt?
3. How should copyright doctrine distinguish the physical method of playing an instrument from the protected musical expression a transcription may communicate?
4. Under what circumstances could computational analysis of tablature, including intermediate copying, qualify as fair use?

## Summary of Findings

The technical answer to the first question is **yes**. A guitar tablature is not a sequence of absolute pitches. Its note events specify strings and frets; the sounding pitches depend on the instrument's open-string tuning. A single unchanged passage can therefore decode into different melodies under different tunings. gtrsnipe constructs candidate **tablature homographs**, tests physical and fingering constraints, and verifies the resulting pitch sequences.

This result has a narrower legal consequence than the assertion that guitar tablature is categorically outside copyright. It means that **coordinate identity alone does not mathematically identify a unique pitch sequence without a tuning assumption**. In an evidentiary setting, that may matter where a dispute rests on matching short, unkeyed passages. It matters less, or not at all, when context supplies the tuning, title, source recording, attribution, arrangement, or other evidence identifying the protected composition.

The legal characterization of a fixed transcription, the inference of actual copying, substantial similarity of protected expression, and fair use remain distinct, fact-sensitive inquiries.

---

## 1. The Representational Distinction

### 1.1. Coordinates and sounding pitches

For a simplified monophonic tablature passage, let

\[
T = ((s_1,f_1), (s_2,f_2), \ldots, (s_n,f_n)),
\]

where \(s_i\) is the string index and \(f_i\) is a nonnegative fret number. In twelve-tone equal temperament, measured in MIDI-style semitone units, a tuning vector \(K\) specifies the open pitch \(K(s)\) of each string. The decoded pitch at event \(i\) is

\[
P_i = K(s_i) + f_i.
\]

The model abstracts away expressive timing, bends, harmonics, muting, and other performance features. Such features may appear explicitly or implicitly in real tablature. Nothing here requires a claim that a full tab is devoid of expressive information; it establishes only that **absolute pitch depends on the tuning**.

A single fret coordinate may sound at a different pitch on a differently tuned instrument, and changing different strings by different amounts can change not just the key but the passage's interval structure.

### 1.2. The tablature homograph

Let \(D(T,K)\) be the pitch sequence obtained by decoding the same fixed tablature \(T\) under tuning \(K\). A tablature homograph is a case in which

\[
D(T,K_A)=A, \qquad D(T,K_B)=B, \qquad A\ne B,
\]

where \(A\) and \(B\) are distinct musical passages. They may, in specially constructed or found examples, be recognizable excerpts from unrelated compositions. The existence of such a representation does not establish anything about how either composition was created or whether an actual publisher copied anyone's work.

For a fixed note-by-note alignment of target passages \(A\) and \(B\), define

\[
\delta_i = b_i-a_i, \qquad r(A,B)=\left|\{\delta_i:1\le i\le n\}\right|.
\]

For notes assigned to a single string, the difference \(b_i-a_i\) must equal the difference between that string's two open tunings. Thus the number of distinct offset values, termed **offset richness** \(r\), supplies a necessary lower bound on the number of strings required. In an idealized instrument with freely selectable string pitches and adequate fret span, the offset classes can be assigned to strings. On an actual guitar, simultaneous notes, string allocation, fret reach, string tension, and ergonomics impose additional constraints.

The demonstrated proposition is therefore precise: a decoded melody is a function of **both** a coordinate sequence and its tuning. Tablature's expressive interpretation is not always recoverable uniquely from unkeyed coordinates alone.

For the constructive implementation and further mathematical restrictions, see the [gtrsnipe homograph documentation](../../app/DESIGN-homograph.md) and the project's [research results](../results/).

### 1.3. A cryptographic analogy, with limits

A homograph resembles a keyed encoding: identical symbols can yield different meaningful outputs under different decoding parameters. The analogy illustrates *decoder-relative interpretation*; it is not a claim that a tab is encrypted, that a particular cipher classification governs it, or that ciphertext cannot embody copyrighted expression. The key in this model is a physically specified tuning vector, not a legal exemption.

---

## 2. Copyright Questions Raised by Coordinate Ambiguity

### 2.1. The statutory boundary between systems and expression

[17 U.S.C. Sec. 102(b)](https://www.govinfo.gov/content/pkg/USCODE-2024-title17/html/USCODE-2024-title17-chap1-sec102.htm) excludes copyright protection for ideas, procedures, processes, systems, and methods of operation as such. The method of locating and sounding notes by selecting a guitar string and fret is functional. But that does not necessarily render *every particular ordered sequence* of such instructions unprotectable, particularly where the sequence communicates an underlying composition or contains original selection or arrangement.

The relevant inquiry is not whether a tab uses functional coordinates **or** embodies musical expression. It can do both. The distinction instead requires identifying the protected expression allegedly taken, the functional elements that remain free for others to use, and the use the defendant actually made of the representation.

### 2.2. Fixation does not require direct human readability

The Copyright Act defines copies broadly enough to include material objects from which a work may be perceived, reproduced, or communicated **with the aid of a machine or device**. See [17 U.S.C. Sec. 101](https://www.govinfo.gov/content/pkg/USCODE-2024-title17/html/USCODE-2024-title17-chap1-sec101.htm). It would therefore be incorrect to infer that machine dependency or tuning dependency alone prevents a representation from being a copyright-law copy. Nor does the possibility of a second valid decoding necessarily erase the first.

A single representation may be capable of conveying two works. That fact does not grant either copyright holder ownership of every abstract coordinate sequence capable of producing the work, and it does not establish that publication of the sequence is invariably lawful. **The use and context still matter.**

### 2.3. Evidentiary consequences: what an unkeyed match does and does not show

A claimant relying on matching coordinate data would need to establish that the defendant copied protected expression, not merely point to the existence of a mathematically reproducible string/fret sequence. A credible homograph may help test whether *raw coordinate coincidence*, viewed in isolation, uniquely supports the inference the claimant proposes.

It would **not** automatically defeat other evidence of copying, shift a statutory burden of proof, negate the relevance of a transcription's title or tuning metadata, or permit the distribution of a labeled full-song transcription without authorization. It also would not prove independent creation; independent creation is a separate factual question.

The most promising potential application is therefore an evidentiary one: **a demonstration that a short, unkeyed coordinate match admits alternative explanations under stated and physically feasible decoding assumptions**. The demonstration is strongest when the alternative is supported by reproducible physical decoding, not merely by choosing an arbitrary and unusable tuning.

---

## 3. Historical Precedent: Mechanical Encodings and Their Legal Treatment

In [*White-Smith Music Publishing Co. v. Apollo Co.*, 209 U.S. 1 (1908)](https://supreme.justia.com/cases/federal/us/209/1/), the Supreme Court held that perforated piano rolls were not statutory copies of musical compositions under the law **then in force**. The case illustrates how novel encoding media can expose uncertainties in legal categories, and it furnishes a historical comparison between readable scores and mechanical instructions.

That result is **not a controlling modern exemption for tablature**. Congress addressed mechanical reproductions in the 1909 Act, and the 1976 Act adopted a substantially broader definition of copies, including those perceptible with the aid of a machine or device. The contemporary argument cannot simply substitute the guitar for the player piano and claim *White-Smith* decides the case.

What remains useful is the historical question *White-Smith* presented: how should law characterize a representation whose relation to a musical work is mediated by a device? gtrsnipe adds a factual complication distinctive to a retunable fretted instrument: the device itself may be reconfigured to decode the **same physical coordinates into different musical passages**.

Whether that additional property changes a result under contemporary copyright law depends on the protected material, the challenged conduct, and the evidentiary record. It should not be presented as an already established doctrinal rule.

---

## 4. Computational Evidence: The gtrsnipe Research Program

### 4.1. Reproducible construction and independent verification

[gtrsnipe](https://github.com/scottvr/gtrsnipe) maps musical events to feasible string/fret positions and implements a homograph search over aligned passages, offset classes, tunings, and instrument constraints. Its distinct operating modes include unrestricted tunings, an *anchored* mode in which the first passage uses a specified tuning, and a *middle* mode in which both performances are retunings of one instrument configuration. The code also supports an **as-written** test: whether a preexisting tab's *actual fingering* can be retuned to sound another passage.

Candidates are checked against available fret positions, simultaneous-string constraints, modeled string-tension limits, and a playability scoring system. Returned solutions are checked by decoding their string/fret assignments under each proposed tuning. The implementation uses bounded searches and heuristic selection in parts of the pipeline; it should not be described as globally optimal over all possible tunings and fingerings without qualifications.

The crucial distinctions for interpretation are:

- **Mathematical possibility:** Does a common unkeyed coordinate sequence exist in an idealized setting?
- **Physical feasibility:** Can realistic strings, tensions, and fretboards realize the candidate?
- **Playability:** Is it ergonomically plausible, rather than merely theoretically fingerable?
- **As-written coincidence:** Does a *particular preexisting transcription* possess a homograph partner without changing its recorded fingering?

Evidence at one level must not silently be promoted into evidence at the next.

### 4.2. Reported experimental observations

The results below are **reported findings from the project's R03, R03b, R04, and R05 studies**, not new calculations made for this memorandum. Consult the [current results directory](../results/) for the reports, data-processing choices, denominators, and subsequent corrections.

| Study | Finding reported in project summary | Proper interpretation / limitation |
| --- | --- | --- |
| R03: tune-family retrieval | Whole-melody offset richness was a weak standalone similarity feature; the reported MAP improvement over a transposition-invariant Hamming baseline was at most 0.006. | A measure's mathematical structure does not guarantee useful melodic retrieval. |
| R03b: phrases and motifs | The reported phrase-level, alignment-based comparison improved MAP by approximately 0.009-0.010 across the evaluated annotators. | Modest, task-specific predictive improvement; reproduce significance estimates and baselines from the study before citing statistical significance. |
| R04: short-passages scan | In the stated sampled folk-pair protocol, reported compatible proportions were about 33% at 8 notes, 8% at 12 notes, and 3% at 16 notes. | These are conditional rates among the studied, rhythm-compatible samples, not estimates for all pairs of copyrighted songs or published tabs. |
| R04: string physics | Selected homograph candidates were reported physically viable at high rates for folk samples (93%-100% in certain conditions), with a range of anchored-mode outcomes for pop datasets. | Specify the candidate-selection denominator, tuning mode, string set, and thresholds. Feasibility is not evidence of ordinary playing practice. |
| R04: ergonomics | 49 of 50 sampled candidates reportedly had a valid physical tab; only 19 were within 50 mapper cost units per note of native fingering, four within 20, and none within five. | A possible shared tab may still be conspicuously unnatural or costly to play. The mapper score is a model, not an independently validated measure of human comfort. |
| R05: as-written matching | The summary reports many partners for sampled eight-note excerpts and no unrelated partners found at 24 and 32 notes under the evaluated conditions. | An observed zero is not a proof of impossibility. As-written identity is materially more constrained than free construction. |

**Reporting requirement.** Before an individual figure is offered as evidence in a legal filing, the linked report should specify the exact corpus version, sample size and pairing procedure, filtering criteria, alignment rule, whether octave changes or transposition were permitted, physical parameters, code revision, random seeds where applicable, and uncertainty intervals. Those details define the population to which the result can responsibly be generalized.

The negative and narrowing results are not incidental. They are part of the finding: homograph prevalence declines with passage length in these experiments; models differ in what they permit; and an existing tab is considerably harder to match than a newly constructed common tab.

### 4.3. A narrower and testable evidentiary proposition

A prospective empirical question is: **For a specified class of unkeyed, length-limited tablature passages, how frequently could a coordinate-based matcher associate the same coordinates with genuinely distinct underlying music under plausible tuning assumptions?** That question can be tested with disclosed corpora and scoring rules. It is not answered merely by showing that one homograph exists; nor does it establish how courts must weigh a given match.

---

## 5. Computational Analysis and the Four-Factor Fair-Use Inquiry

A separate issue arises when a researcher copies or parses copyrighted material to study its structural or functional properties. Fair use under [17 U.S.C. Sec. 107](https://www.govinfo.gov/content/pkg/USCODE-2024-title17/html/USCODE-2024-title17-chap1-sec107.htm) requires consideration of the challenged **use** under all four statutory factors. The fact that gtrsnipe uses mathematics or dynamic programming is not, by itself, a fair-use exemption.

### Factor 1: Purpose and character

Analysis of a work to measure fingering geometry, tune similarity, or homograph prevalence can have a purpose distinct from supplying a performable substitute for the original. That distinction may favor fair use in an appropriately delimited research use, especially where the output consists of aggregated measurements rather than redistributed tabs. It is not dispositive. The Supreme Court has emphasized that the purpose of the *specific challenged use* matters; calling a technology transformative in the abstract is insufficient. See [*Andy Warhol Foundation v. Goldsmith*, 598 U.S. 508 (2023)](https://supreme.justia.com/cases/federal/us/598/21-869/).

### Factor 2: Nature of the work

The underlying musical compositions are creative works entitled to substantial copyright protection. At the same time, functional fingering conventions and the abstract fretboard coordinate system implicate the exclusion of methods and systems under Section 102(b). Those observations bear on the analysis; they do not automatically make the transcribed compositions unprotected.

### Factor 3: Amount and substantiality

Certain whole-passage or whole-work analyses may require processing a complete source to obtain a valid result. Other research questions, including short-phrase searches, do not. Any claim of necessity should identify the algorithm, its actual input requirements, and why a less extensive use would not serve the specified analytical purpose. Private intermediate processing and redistribution of complete playable transcriptions are different activities.

### Factor 4: Market effects

A research report that discloses aggregate homograph rates or physical constraints is ordinarily less substitutive than a downloadable, playable tab of a commercially exploited composition. But gtrsnipe itself can *produce* playable tabs, so different outputs and distribution practices must be evaluated separately. Both actual and reasonably cognizable potential market effects may matter.

### Relevant but non-dispositive analogies

In [*Sega Enterprises Ltd. v. Accolade, Inc.*, 977 F.2d 1510 (9th Cir. 1992)](https://openjurist.org/977/f2d/1510/sega-enterprises-ltd-v-accolade-inc), the court accepted fair use for certain intermediate copying undertaken to learn unprotected functional aspects of computer software. In [*Authors Guild v. Google, Inc.*, 804 F.3d 202 (2d Cir. 2015)](https://law.justia.com/cases/federal/appellate-courts/ca2/13-4829/13-4829-2015-10-16.html), copying books to support search and limited snippets was held fair use on that record. Neither case resolves rights in musical transcriptions or grants blanket authorization to ingest and republish protected music.

The research-use argument is strongest when the record distinguishes **what was copied internally, why that amount was needed, what was exposed externally, and whether the output competes with licensed expressive uses**.

---

## 6. Historical Context: OLGA and the Cost of Unlitigated Questions

The On-Line Guitar Archive (OLGA) and similar community projects supplied amateur transcriptions long before algorithmic homograph discovery was practical. Their history illustrates the consequences of threatened copyright litigation for volunteer-run technical and cultural archives, but it should not be rewritten as a judicial holding in either direction.

Contemporary reporting documents a 1998 shutdown following a threat from the **Harry Fox Agency** and renewed pressure in 2006 from representatives of the **National Music Publishers' Association** and **Music Publishers Association**, followed by OLGA's withdrawal. These are distinct episodes and should not be attributed interchangeably. See the [*Washington Post*, July 1998](https://www.washingtonpost.com/archive/business/1998/07/20/no-music-for-site-readers/935b2669-2849-4c41-9294-59c7c5d31103/), [*Ars Technica*, August 2006](https://arstechnica.com/uncategorized/2006/08/7498/), and [*InfoWorld*, January 2007](https://www.infoworld.com/article/2196474/publishers-strike-wrong-chord-with-musicians.html).

No result reported here demonstrates that the old archives' full-song distribution was lawful, that their operators would have prevailed in court, or that the market for tablature became monopolized as a result. The more defensible historical inquiry is whether the expense and risk of litigation prevented technical distinctions about amateur transcription, mechanical notation, and independent creation from receiving full adversarial examination.

The homograph work supplies an additional tool for such examination today. It cannot retroactively decide those cases.

---

## 7. Potential Uses in a Concrete Dispute

For a genuine claim based partly on a short coordinate excerpt, an expert could:

1. Preserve the precise accused tab and surrounding metadata, including title, tuning declarations, provenance, layout, and timing.
2. Reconstruct the claimed coordinate matching without silently assuming standard tuning.
3. Identify plausible alternative tuning vectors and perform the actual pitch decoding.
4. Test whether alternatives are physically feasible on a specified instrument and disclose discomfort or contrived fingering.
5. Compare the matched passage length, as-written behavior, and relevant source-population baselines with the project's published experiments.
6. Distinguish what these experiments show about **representational uniqueness** from separate evidence about access, copying, substantial similarity, distribution, and fair use.

No one of these steps warrants an automatic ruling. Together, they could make a technical record more informative and prevent an assumption about physical notation from being treated as a measured fact.

## 8. Conclusion

An unchanged sequence of guitar string-and-fret coordinates can produce different pitch sequences under different tuning vectors. gtrsnipe demonstrates that property constructively and reports empirical studies of its frequency and physical limitations. The project thereby supplies an explicit model of a distinction that can be obscured when guitar tablature is treated as though its coordinates uniquely identify absolute notes.

The consequence is **not** that tablature is categorically uncopyrightable, that a second decoding defeats any first owner's rights, or that research software is automatically exempt from infringement liability. The defensible contribution is narrower and potentially more useful: **the strength of an inference from coordinate identity depends on the decoding assumptions, the length and context of the excerpt, and the physical and statistical plausibility of alternative explanations**.

A future court or litigant may find that distinction immaterial in a case involving a fully attributed transcription of a familiar song. In a dispute resting on short, isolated, unkeyed coordinate matches, however, the distinction may be exactly the fact that requires examination.

---

## Authorities and Research Record

### Statutes and decisions

- [17 U.S.C. Sec. 101: Definitions](https://www.govinfo.gov/content/pkg/USCODE-2024-title17/html/USCODE-2024-title17-chap1-sec101.htm).
- [17 U.S.C. Sec. 102: Subject matter of copyright](https://www.govinfo.gov/content/pkg/USCODE-2024-title17/html/USCODE-2024-title17-chap1-sec102.htm).
- [17 U.S.C. Sec. 107: Fair use](https://www.govinfo.gov/content/pkg/USCODE-2024-title17/html/USCODE-2024-title17-chap1-sec107.htm).
- [*White-Smith Music Publishing Co. v. Apollo Co.*, 209 U.S. 1 (1908)](https://supreme.justia.com/cases/federal/us/209/1/).
- [*Sega Enterprises Ltd. v. Accolade, Inc.*, 977 F.2d 1510 (9th Cir. 1992)](https://openjurist.org/977/f2d/1510/sega-enterprises-ltd-v-accolade-inc).
- [*Authors Guild v. Google, Inc.*, 804 F.3d 202 (2d Cir. 2015)](https://law.justia.com/cases/federal/appellate-courts/ca2/13-4829/13-4829-2015-10-16.html).
- [*Andy Warhol Foundation for the Visual Arts, Inc. v. Goldsmith*, 598 U.S. 508 (2023)](https://supreme.justia.com/cases/federal/us/598/21-869/).

### Project materials

- [Results and experimental revisions: R03, R03b, R04, R05](../results/).
- [Tablature homograph design and constraints](../../app/DESIGN-homograph.md).
- [gtrsnipe source repository](https://github.com/scottvr/gtrsnipe).
- [Original satirical companion: *IANAL.md*](IANAL.md).

**Versioning note for prospective legal use:** A link to a report on the mutable `main` branch is helpful for ordinary research, but poor as an evidentiary snapshot. For any cited result, retain a commit-SHA permalink, script and dataset versions, and generated outputs or hashes. This memorandum deliberately points to the living results index; a subsequent legal brief should cite a fixed revision of each individual report.

<!-- Editorial follow-up: Replace the results-directory links beside R03/R03b/R04/R05 with verified relative paths to the individual reports once their exact names are confirmed. Reconcile all numerical assertions against current reports. -->

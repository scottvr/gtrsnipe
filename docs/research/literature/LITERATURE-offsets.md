# Prior art: offset vocabulary, tab homographs, offset metrics (backlog R06)

A literature search made before any novelty claim, for
[`coupled_transposition_structure.md`](../theory/coupled_transposition_structure.md) and the homograph
work. Compiled 2026-09-26 by a Claude research agent (web search). The "Verified" column says
how each source was checked: *read* means the full text or PDF was opened, *abstract* or
*listing* means less. **Re-check every citation before it goes in the paper**, especially the
rows not marked read.

## Bottom line

- **The object is known. Using it as a measure looks new.** Mäkinen, Navarro & Ukkonen (2005,
  §6) define the set of aligned transpositions T = {tᵢ = bᵢ − aᵢ} and note |T| = O(m). They use
  |T| only as a running-time bound, and take the *mode* of T ("the most voted transposition
  wins") to get transposition-invariant Hamming distance. Nothing found uses |T| (richness)
  or H(δ) as a similarity or distance.
- **Every neighbouring measure uses the mode, a spread/L1 value, or a switch count. None
  counts distinct offsets.**
  - Mode: MNU's Hamming distance, SIAM/P2, Straus's "consistency", jSymbolic's "prevalence of
    most common vertical interval".
  - L1 or spread: SIMILE's `diff` (this is TV), Straus's "offset", SAD/MAD, (δ,γ)-matching.
  - Switches: Allali et al. (a penalty per local transposition), Lemström–Mäkinen (minimum
    number of pieces), edit distance on the interval encoding.
- **Risk, richness as a similarity measure: low to moderate.** The risk is a reviewer calling it
  obvious, not an earlier claim. Credit MNU §6 for the object and claim the use.
- **Risk, the tab homograph: low in the scholarship.** The ingredients are old:
  - Tablature and scordatura notation (Griffschrift) mean something only relative to a tuning:
    Biber, lyra viol, the French lute's accords nouveaux.
  - Allen & Goudeseune (2011) define the per-string retuning vector.
  - De Souza (2020) treats scordatura as voice leading between tunings.

  What was not found: one tab built to play two given, unrelated melodies; a solver for the
  tuning pair; or the "≤ 6 classes of constant offset" criterion.
- **The legal literature has nothing on this.**
  - Law notes on tabs treat them as copies or derivative works; none raises the ambiguity
    tunings create.
  - Rahmatian (2024) states the doctrine the construction instantiates: "similarity of
    notation without similarity of the listening experience points away from infringement."
  - The philosophical hook is Goodman's requirement of semantic disjointness.
  - Nobody has made the reductio.
- **Risk, the metric results: high if presented as new theorems.**
  - r_AC ≤ r_AB·r_BC and H(δ_AC) ≤ H(δ_AB) + H(δ_BC) are one-liners: δ_AC is a function of
    the coupled pair, so H(f(Z)) ≤ H(Z), then subadditivity.
  - That other Rényi orders fail follows from the classical fact that Rényi entropy is not
    subadditive for α ∉ {0, 1}. Choose offset values whose pairwise sums are all distinct;
    then H_α(δ_AC) equals the joint entropy, and any non-subadditive joint distribution becomes
    a triangle violation.
  - Present these as applications of known results.
- **Order ∞, carefully.** The metric is 1 − p_max (the complement of the Berger–Parker index,
  i.e. normalized transposition-invariant Hamming), not log(1/p_max). Min-entropy is not
  subadditive: joint probabilities .3/.3/.3/.1 with marginals .6/.4 give 1.74 bits, against a
  sum of 1.47.

## 1. Offset vocabulary as a melodic measure

| Citation | Defines | Relation to r / H(δ) | Verified |
|---|---|---|---|
| Mäkinen, Navarro & Ukkonen, "Transposition invariant string matching," *J. Algorithms* 56(2):124–153 (2005) | Transposition-invariant Hamming, SAD, MAD and (δ,γ). §6 defines T = {bᵢ − aᵢ} for aligned strings | **The closest.** Our offset set, but they use only its mode; \|T\| is a runtime bound | read; doi:10.1016/j.jalgor.2004.07.008 |
| Allali, Ferraro, Hanna & Iliopoulos, SPIRE 2007, LNCS 4726:26–38 | Dynamic-programming alignment with multiple local transpositions | Penalizes switches. Ferraro, Hanna, Imbert & Izard (ISMIR 2009 §2.2): "a penalty … is also applied to each local transposition". The agent inferred (not confirmed) that the DP state holds only the current transposition, so returning to an earlier offset is charged again | abstract; doi:10.1007/978-3-540-75530-2_3; ISMIR 2009 PDF read |
| Allali et al., *Fundamenta Informaticae* 97(3):331–346 (2009) | Polyphonic framework, one matrix per transposition | Same as above | read; doi:10.3233/FI-2009-205 |
| Lemström & Mäkinen, CPM 2003 (LNCS 2676:237–253); *J. Discrete Algorithms* 3(2–4):248–266 (2005) | Minimum number of pieces a pattern is split into across tracks | Also a switch count: going back to a track costs a new piece | listing; doi:10.1016/j.jda.2004.08.008 |
| Lemström & Ukkonen, AISB 2000, pp. 53–60 | Interval encoding inside edit distance | Hamming distance on intervals = our S | listing only |
| Cambouropoulos, Crochemore, Iliopoulos, Mouchard & Pinzon, *Int. J. Computer Math.* 79(11):1135–1148 (2002) | δ- and γ-approximate matching | δ bounds max\|δᵢ\| and γ bounds Σ\|δᵢ\|; with transposition invariance they bound the spread. Never a count | listing; doi:10.1080/00207160213939 |
| Ukkonen, Lemström & Mäkinen, ISMIR 2003 | P1/P2/P3 point-set matching | P2 = mode of the translation vectors over all note pairs (unaligned) | read; doi:10.5281/zenodo.1417477 |
| Meredith, Lemström & Wiggins, *JNMR* 31(4):321–345 (2002) | SIA vector table, maximal translatable patterns (MTPs), SIATEC/COSIATEC | Vectors are within one piece; patterns are ranked by MTP size or compression, never by the number of distinct vectors. COSIATEC's cover of a piece by a few translated patterns is a cousin of the ≤ 6 classes | DOI resolves (10.1076/jnmr.31.4.321.14162); not opened |

## 2. Catalogues of melodic similarity measures

| Citation | Defines | Relation | Verified |
|---|---|---|---|
| Müllensiefen & Frieler, *Computing in Musicology* 13:147–176 (2004); 2006 chapter, doi:10.1007/3-540-34416-0_32; SIMILE docs v0.3 (2006) | About 50 measures | **`diff`/`diffexp` = L1 distance between interval sequences = our TV: prior art for TV.** Transposition is chosen from the differences of the highest, lowest, most common and mean pitches. Their "count distinct" counts n-grams, not offsets | SIMILE docs read; CM13 via a listing |
| Janssen, van Kranenburg & Volk, *JNMR* 46(2):118–134 (2017) | Six measures: CD, CBD, ED, LA, SIAM, WT | SIAM = max_T \|MTP\|/n (a mode, unaligned). Transposition is fixed by pitch-histogram intersection (van Kranenburg, Volk & Wiering, *JNMR* 42(1):1–18, 2013) | doi:10.1080/09298215.2017.1316292; content read in Janssen's 2018 thesis, ch. 4 |
| Velardo, Vallati & Jan, *Computer Music Journal* 40(2):70–83 (2016) | Survey and taxonomy | Not checked in full | abstract; doi:10.1162/COMJ_a_00359 |
| Lewin, "Re: Intervallic relations between two collections of notes," *JMT* 3(2):298–301 (1959); *GMIT* (1987) | IFUNC(X,Y)(i) = #{(x,y): y − x = i} | **Confirmed unaligned (all pairs).** Our δ histogram is IFUNC restricted to the alignment diagonal | doi:10.2307/842856; definition via secondary sources |
| McKay, Cumming & Fujinaga, jSymbolic 2.2, ISMIR 2018 | Vertical-interval histogram; prevalence of the most common vertical interval | If A and B are simultaneous voices, δ *is* the vertical-interval sequence. The histogram and the modal share describe one piece, not a distance, and there is no distinct count | read |

## 3. Voice-leading geometry

| Citation | Defines | Relation | Verified |
|---|---|---|---|
| Callender, Quinn & Tymoczko, *Science* 320:346–348 (2008) | OPTIC quotient spaces | The offset vector is a voice leading in ordered pitch space; transposition invariance is the T quotient | doi:10.1126/science.1153021 |
| Tymoczko, *Science* 313:72–74 (2006); Hall & Tymoczko, *Amer. Math. Monthly* 119(4):263–283 (2012) | Voice-leading size as norms of the displacement vector | Norms, not distinct counts | doi:10.1126/science.1126287; doi:10.4169/amer.math.monthly.119.04.263 |
| Straus, *Music Theory Spectrum* 25(2):305–352 (2003); *JMT* 49(1):45–108 (2005) | Uniformity as **offset** (semitones from a crisp transposition) or **consistency** (number of voices moving the same distance); fuzzy transposition | Offset is L1-like; consistency is our order-∞ measure. No "number of distinct displacements" anywhere | doi:10.1525/mts.2003.25.2.305; doi:10.1215/00222909-2007-002; definitions via De Souza 2020 ¶1.2 |
| De Souza, "Instrumental Transformations in Biber's Mystery Sonatas," *MTO* 26.4 (2020) | Scordatura as voice leading between tunings, measured with Straus's criteria | **Very close to our per-string offset vector.** He measures how uniform a retuning is, not tab reuse across songs | read; doi:10.30535/mto.26.4.1 |

## 4. Prior art for the tab homograph

| Citation | What it does | Relation | Verified |
|---|---|---|---|
| Allen & Goudeseune, "Topological Considerations for Tuning and Fingering Stringed Instruments," arXiv:1105.1383 (2011) | "Retuning cipher" = the difference of two tuning vectors, applied as fret offsets to *preserve* pitch; listeners must find the "hidden" tuning | **The exact dual of the homograph**: same sound from a different tab, where ours is the same tab with a different sound. Must cite | read |
| De Souza, "Fretboard Transformations," *JMT* 62(1):1–39 (2018) | Transformations on the fret × string space | The framework the offsets live in | doi:10.1215/00222909-4450624 |
| De Souza 2020, on Biber's Griffschrift | Notated fingering differs from the sounding pitch; "subject and answer have the same fingering" | Same notation, different sound, but one piece and one intended tuning | as in §3 |
| Lyra-viol tunings; French lute *accords nouveaux* | Many tunings; tablature means something only relative to one | Known to players; no deliberate encoding of two songs found | web sources only |
| StegTab (steganography in guitar tablature) | Hides bits in redundant fingerings | Keeps pitch fixed; does not retune | **UNVERIFIED** (authors and venue unknown) |
| Seeger, *Musical Quarterly* 44(2):184–195 (1958); Kanno, *Contemporary Music Review* 26(2):231–254 (2007) | Prescriptive vs. descriptive notation; action notation | Frames tab as action notation | doi:10.1093/mq/XLIV.2.184; doi:10.1080/07494460701250890 |
| Goodman, *Languages of Art*, 2nd ed. (1976), 186–87 | Score compliance; semantic disjointness; the "Beethoven's Fifth to Three Blind Mice" sorites | A tab without a tuning violates semantic disjointness; the reductio is a one-step counterpart to his sorites | via the Stanford Encyclopedia of Philosophy |
| Gary, 9 Vand. J. Ent. & Tech. L. 831 (2007); Simon, 50 Ariz. L. Rev. 611 (2008); Kempema, 49 Wm. & Mary L. Rev. 2265 (2008) | Tabs as infringement / fair use | None raises tuning ambiguity (Simon and Kempema full texts searched for "tuning") | Simon, Kempema read; Gary as cited |
| Rahmatian, "The Musical Work in Copyright Law," *GRUR Int.* 73(1):18–33 (2024) | "Similarity of notation without similarity of the listening experience points away from infringement" | The doctrine the construction instantiates | doi:10.1093/grurint/ikad105 |
| Selfridge-Field, 16 Colo. Tech. L.J. 249 (2018); Cronin, *Computing in Musicology* 11:187–210 (1998); Fishman, 131 Harv. L. Rev. 1861 (2018) | Notation vs. sound; melody-centrism | No tab/tuning argument found | Selfridge-Field read; others via listings |
| *Skidmore v. Led Zeppelin*, 952 F.3d 1051 (9th Cir. 2020) (en banc); *Williams v. Gaye*, 895 F.3d 1106 (9th Cir. 2018); *Gray v. Hudson*, 28 F.4th 87 (9th Cir. 2022) | Under the 1909 Act the deposit copy defines the work; commonplace building blocks | Hook: a tab as the deposit copy would not pin the work down. (The appeal is *Gray v. Hudson*; the district court case is *Gray v. Perry*) | opinions seen |

Computational work: MIDI-to-tab and fingering systems either take the tuning as fixed or, like
Allen & Goudeseune, treat it as a variable to optimize for playability. No system was found that
infers a pair of tunings mapping one fingering onto two melodies.

Searched without a hit: "tab/tablature homograph", same tab in different tunings giving a
different song, tablature steganography via retuning, copyright plus scordatura or alternate
tuning, cross-tuning in fiddle and banjo traditions, puzzle canons.

## 5. Math sources

- **Sumsets and entropy.**
  - Ruzsa, "Sumsets and entropy," *Random Structures & Algorithms* 34(1):1–10 (2009),
    doi:10.1002/rsa.20248.
  - Tao, *Combinatorics, Probability and Computing* 19(4):603–639 (2010),
    doi:10.1017/S0963548309990642.
  - Both concern *independent* summands (Tao's entropic Ruzsa distance included). Our offsets
    are *coupled* by the alignment, so the elementary argument is the right one. Keep H(δ)
    distinct from Ruzsa distance for readers.
- **Diversity indices.**
  - Hill, *Ecology* 54(2):427–432 (1973), doi:10.2307/1934352.
  - Jost, *Oikos* 113(2):363–375 (2006), doi:10.1111/j.2006.0030-1299.14714.x.
  - Berger & Parker, *Science* 168:1345–1347 (1970), doi:10.1126/science.168.3937.1345: the
    modal-share index.
- **Why only orders 0 and 1.**
  - Aczél, Forte & Ng, "Why the Shannon and Hartley entropies are 'natural'," *Adv. Appl.
    Probab.* 6(1):131–146 (1974), doi:10.2307/1426210. Only linear combinations of Shannon and
    Hartley entropy are both additive and subadditive.
  - Linden, Mosonyi & Winter, *Proc. R. Soc. A* 469:20120737 (2013), doi:10.1098/rspa.2012.0737.
    For classical distributions and α ≠ 0, 1, the only universal inequalities are
    non-negativity and monotonicity.
  - Madiman–Wang–Woo's Rényi sumset results concern independent sums, so they don't apply here.

  **Consequence for the structure note §4.4**, which makes "no metric claim for other orders
  without an order-specific proof". The failure is in fact general. For any α ∉ {0, 1}:
  1. Take a joint distribution (X, Y) with H_α(X, Y) > H_α(X) + H_α(Y); one exists because
     Rényi entropy is not subadditive at those orders.
  2. Give X and Y values whose sums x + y are all distinct, and approximate the probabilities by
     rationals; Rényi entropy is continuous, so the inequality survives.
  3. Set B = A + X and C = B + Y. Then δ_AC = X + Y determines the pair (X, Y), so
     d_α(A,C) = H_α(X, Y) > d_α(A,B) + d_α(B,C).

## Suggested wording (for the paper)

> Mäkinen, Navarro and Ukkonen (2005) define the set of pointwise transpositions between
> aligned strings but use only its mode (transposition-invariant Hamming distance);
> transposition-aware alignment (Allali et al. 2007) and multi-track splitting (Lemström &
> Mäkinen 2005) charge each *change* of transposition. We instead count the *vocabulary* of
> offsets, a Hill number of order 0. Its triangle inequality, like that of its order-1
> counterpart, follows from elementary sumset and subadditivity bounds, and no other Rényi
> order qualifies, which reflects the classical characterization of Aczél, Forte and Ng
> (1974). On a fretted instrument this vocabulary has a physical reading. Building on the
> per-string retuning vectors of Allen & Goudeseune (2011) and De Souza's (2018, 2020)
> treatment of scordatura as voice leading, we show that one tablature can denote unrelated
> melodies under two tunings: a concrete case of Goodman's semantic-ambiguity problem for
> notation that, to our knowledge, the copyright literature on tablature has not addressed.

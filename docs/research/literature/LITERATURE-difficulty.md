# Prior art: estimating the difficulty of a piece from its score or tab (backlog M03)

A literature search made before designing gtrsnipe's tab difficulty measure (M03). Compiled
2026-11-07 by Claude (web search; six papers read in full from their PDFs, the rest from
abstracts and listings). The "Verified" column uses the same levels as
[`LITERATURE-offsets.md`](LITERATURE-offsets.md): *read* means the full text was opened,
*abstract* or *listing* means less. **Re-check every citation before it goes in a paper.**
Copies of the PDFs read are in `runs/m03-literature-2026-11-07/` (local, not shipped).

## Bottom line

- **The problem has a name and a small literature:** "score difficulty" or "playability"
  estimation, mostly for piano (2012 to 2025), with three guitar papers (2017, 2023, 2025).
  Nobody has published a measure for a *tab* of arbitrary texture validated against graded
  repertoire; the closest is Rodríguez & Klapuri (CMMR 2025), on a private platform catalogue.
- **The features that work are the ones gtrsnipe already computes or nearly does.** Hand
  (index-finger) travel, number of fingers down, stretch, barre, chord-change rate, notes per
  second, position shifts, and repetitiveness. Pitch-only descriptors (entropy, range,
  Lempel-Ziv complexity of pitch sets) carry the piano results; on guitar the kinematic ones
  do ("kinematics drive performance", CMMR 2025).
- **Two guitar papers independently define hand position as the index finger**, the barre
  fret if there is one, else the lowest fretted fret (Ariga et al. 2017; Hori & Sagayama
  2016 as fret minus finger number plus one). This is the position of scottvr's 2026-11-07
  note, now with two citations. Ariga et al. measured it: mean index-finger movement
  correlates 0.55 with expert difficulty ratings of classical tabs, and the mean number of
  fingers down 0.51 (five raters, 50 ratings, 7-point scale).
- **Time between onsets belongs in the movement cost.** Hori & Sagayama scale the
  hand-movement penalty by the inter-onset interval (a Laplace kernel with scale equal to
  the time between the two notes), so the same shift is cheap when there is time for it.
  gtrsnipe's movement term ignores time entirely.
- **Aggregation matters.** CMMR 2025 found per-song *means* of the per-note difficulties beat
  cumulative sums, and the quadratic mean beat every other mean; Vélez Vásquez et al. found
  length alone predicts almost nothing. Hori & Sagayama argue the *hardest* move (a minimax
  objective) is what makes a phrase hard, not the sum, and show the minimax fingering is the
  one guitarists choose. So a difficulty measure wants at least a mean and a maximum, not a
  total.
- **Ceiling.** The best guitar result is a mean squared error of 0.94 on a 10-level scale
  (adjacent accuracy 0.90), which the authors argue is at the level of annotator disagreement
  (about plus or minus one level). The best piano result on 9 levels is about 40% exact
  accuracy. A rank correlation with graded repertoire is the realistic validation, not exact
  level prediction.
- **Ground truth exists for guitar and is public as lists**, not as scores: the RCM
  Classical Guitar Syllabus (2018) names 413 pieces across Preparatory and Levels 1 to 8;
  Trinity and ABRSM publish grade lists; Delcamp's free editions are organised in grades 1
  to 12 (PDF only). The scores themselves must come from elsewhere (ClassClef's 6,000 tabs
  with MIDI and Guitar Pro files, GAPS's 300 MusicXML tabs, classtab.org's ASCII tabs) and be
  matched by title and composer, the way the Piano Syllabus dataset was built.

## 1. Guitar

| Citation | What it measures and how | Validation | Relevance to M03 | Verified |
|---|---|---|---|---|
| Ariga, Fukayama & Goto, "song2guitar: a difficulty-aware arrangement system for generating guitar solo covers from polyphonic audio of popular music," ISMIR 2017, pp. 568–574 | Two tab features: mean movement of the **index finger** (barre fret if any, else the lowest fretted fret) and mean number of fingers pressing. Used as knobs on an HMM arrangement (EASY/NORMAL/HARD) | Five proficient guitarists rated 10 classtab.org tabs each on a 7-point scale, left hand only: correlation 0.55 (index movement) and 0.51 (fingers), R² 0.30 and 0.26. A user found EASY (sparse single notes) harder than NORMAL (chords): familiar chord shapes are easier than irregular few-note fingerings; 16ths harder to read than 8ths | The index-finger definition of position, with a measurement; the warning that fewer notes is not easier; classtab.org as a tab source gtrsnipe can read | read (ISMIR archive PDF) |
| Hori & Sagayama, "Minimax Viterbi algorithm for HMM-based guitar fingering decision," ISMIR 2016, pp. 448–453 | Transition cost between left-hand forms (string, fret, finger): Laplace kernel on the **index-finger position** difference `ifp = fret − finger + 1`, with scale = inter-onset time (long gaps make moves cheap); times 1/(1+\|string change\|); times a per-finger ease (index 0.35, middle 0.3, ring 0.25, pinky 0.1). Decodes by **minimax** (maximize the smallest transition probability) instead of the product | Three monophonic examples (C major scale, Romance Anonimo): minimax picks the fingering guitarists use, avoids the pinky and string changes | A hardest-move statistic; time in the movement cost; finger-indexed form cost (M06); the same first-order structure as our Viterbi, so a minimax objective is one line away (also the parked "different objectives" idea) | read |
| Vélez Vásquez, Baelemans, Driedger, Zuidema & Burgoyne, "Quantifying the ease of playing song chords on the guitar," ISMIR 2023, pp. 725–732 | A seven-criterion rubric for **rhythm guitar** from teacher interviews, each 0–3, weighted: uncommonness of chord (3), chord finger positioning = stretch/cramp (3), fingering difficulty = fingers used and barre (2), repetitiveness (2), right-hand complexity = skipped inner strings (2), chord progression speed (1), beat difficulty (0, recommended dropped). Rule-based baseline: TF-IDF over chords of per-chord heuristics (fret span; fingers + barre; strummed strings), average chord duration | One expert annotated 200 McGill Billboard songs (31,205 chords); test-retest within 5 points (sd 6.6); partial-credit model reliability. LSTM on chord symbols beat the rules (ordinal loss 5.3 vs 12.4 on the aggregate); length-only predicts nothing | The rubric as a checklist for a chords-and-strumming profile; TF-IDF "uncommonness" as a feature we lack; evidence that stretch and unfamiliar shapes dominate perceived difficulty | read |
| Rodríguez & Klapuri, "Educational profiling of guitar tablature: tools to foster self-guided learning," CMMR 2025 (Zenodo 17496528) | Per-note descriptors from a tab (string, fret, finger given): motor-control surprisal (n-gram PPM-C surprise of chord shape, neck position, fingering, rhythm; offbeatness; counting) and biomechanics (elastic strain, pressing force, hand and finger relocation speed, wrist and finger repositioning speed, pick repositioning, meter-picking alignment), each quantised to deciles over the catalogue; plus about 650 rule-based tags ("partial barre", "thick strings", "16ths") | 5,000 platform arrangements (Simply-Guitar-like), expert syllabus levels 1–10 (single annotator each; guidelines: level 1 = E/Em/Am down-strums, first position; 2 = up to fret 5 no pinky; 5 = syncopation, hammer-ons; 8 = full barres, bends). XGBoost on 15 tag SVD + 15 difficulty means: MSE 0.94, MAE 0.66, adjacent accuracy 0.90; linear regression 1.07. Means beat sums; quadratic mean best; kinematic descriptors carry the prediction; benchmark descriptors of the two papers above: MSE 1.56 | The nearest published design to M03; its level guidelines are a usable rubric for our own labels; the result ceiling; the finding that time-related (kinematic) features are the consistent ones. Data and code not released | read |
| Go, Kim et al., "Automatic difficulty level rating for guitar tablatures," DLSU bachelor's thesis, 2016 | Linear regression on tab features | R² about 0.28 | Weak; listed for completeness | listing |
| Heijink & Meulenbroek, "On the complexity of classical guitar playing: functional adaptations to task constraints," *J. Motor Behavior* 34(4):339–351 (2002) | Motion capture of six professionals: hand position on the neck, finger span and hand repositioning as the determinants of left-hand complexity; players keep joints mid-range and exploit timing tolerance | Experimental | The biomechanical basis for position, span and shifts as the three movement costs; the nut/bridge discomfort of scottvr's note is the "joints mid-range" principle | abstract; doi:10.1080/00222890209601952 |
| Radisavljevic & Driessen, "Path difference learning for guitar fingering problem," ICMC 2004 | Learns DP cost weights from published tabs | | The learned-weights idea in the parking lot, for guitar | listing |

## 2. Piano (where the field started)

| Citation | What it measures and how | Validation | Relevance | Verified |
|---|---|---|---|---|
| Sébastien, Ralambondrainy, Sébastien & Conruyt, "Score Analyzer: automatically determining scores difficulty level for instrumental e-learning," ISMIR 2012, pp. 571–576 | Seven criteria from MusicXML: playing speed (tempo × shortest significant value), fingering (DP cost functions), hand displacement (ratio of jumps > 12 semitones within 2 beats), polyphony (chord ratio), harmony (accidentals ratio), irregular rhythm (polyrhythm ratio), length (pages or bars) | PCA + clustering of 50 conservatory pieces into three level classes, checked against pianists | The original checklist; "displacement only counts if fast" is the time-scaled movement idea | read |
| Chiu & Chen, "A study on difficulty level recognition of piano sheet music," IEEE ISM 2012 | Extends the list: pitch entropy, pitch range, average pitch, displacement rate (weighted large jumps), average inter-onset interval, playing speed, chord ratio, fingering difficulty | 159 pieces from 8notes, machine learning | Descriptor set reimplemented by RubricNet below | listing (features from the 2024 reimplementation) |
| Ramoneda, Tamer, Eremenko, Serra & Miron, "Score difficulty analysis for piano performance education based on fingering," ICASSP 2022 | Fingering-derived features (from an automatic fingering model) and a GRU with attention; Mikrokosmos-difficulty dataset (147 pieces, 3 levels from Bartók's own ordering) | Fingering features beat notes-only; segment-level feedback | Fingering as the carrier of difficulty, which for guitar is the tab itself | abstract |
| Ramoneda, Jeong, Eremenko, Tamer, Miron & Serra, "Combining piano performance dimensions for score difficulty classification," *Expert Systems with Applications* 238 (2024), doi:10.1016/j.eswa.2023.121776 | CIPI dataset: 652 classical pieces, 9 levels from Henle Verlag, expert-checked; an ensemble over performance dimensions | 39.5% balanced accuracy on 9 levels, median square error 1.1 | The piano ceiling; Henle levels as expert ground truth, the analogue of RCM grades | abstract |
| Ramoneda, Lee, Jeong, Valero-Mas & Serra, "Can audio reveal music performance difficulty? Insights from the Piano Syllabus dataset," arXiv 2403.03947 (2024), *IEEE TASLP* 2025 | PSyllabus: 7,901 pieces, 11 levels, labels **compiled from exam syllabi** (ABRSM, RCM, Trinity and others), audio via YouTube links, with MIDI and CQT | CRNN with attention | The recipe for a guitar graded set: syllabus lists give the labels, scores come from elsewhere | abstract |
| Ramoneda et al., "Towards explainable and interpretable musical difficulty estimation: a parameter-efficient approach" (RubricNet), arXiv 2408.00473 (2024) | White-box model: one linear + tanh per descriptor, summed, sigmoid; descriptors pitch entropy, pitch range, average pitch, displacement rate, average IOI, pitch-set Lempel-Ziv complexity | CIPI: 41.4% on 9 levels (MSE 1.7); MKD 79.6% on 3 levels. Average IOI and average pitch contribute little; tempo missing for 23% of scores | The model shape to copy if we fit weights: rubric-like, few parameters, ordinal loss; the warning that averaging hides fast and slow sections | read (HTML) |

## 3. Ground truth for guitar

| Source | What it gives | Format | Access | Verified |
|---|---|---|---|---|
| RCM Classical Guitar Syllabus, 2018 edition (rcmusic.com, `S47_GuitarSyllabus_ONLINE_2018_F.pdf`); full piece list reproduced at dacapomusic.ca | 413 pieces: Preparatory 38, Levels 1–8 between 38 and 55 each, repertoire and etudes listed separately; composers from Sor, Carulli, Aguado, Giuliani to Brouwer, York, Koshkin | Lists (composer, title, opus) | Public | read (the Da Capo list) |
| Trinity College London classical guitar (from 2020; no end date), Initial to Grade 8 | Grade lists; the pieces are in Trinity's own books, the older repertoire (Carulli, Sagreras, Dowland) exists in free editions | Lists | Public lists, paid books | listing |
| ABRSM guitar syllabus (2019 booklet, pp. 16–31) | Grade lists 1–8 | Lists | Public PDF | listing |
| Delcamp (classical-guitar-sheet-music.com / delcamp.net), J.-F. Delcamp's free editions | Repertoire in grades 1–12 (beginner 1–4, intermediate 5–8, advanced 9–12), thousands of pages, tab editions for the lower grades | PDF only | Free, terms not stated | abstract (site pages) |
| ClassClef (classclef.com) | About 6,000 classical tabs with MIDI, 1,000 scores, Guitar Pro files; an "Easy Pieces" category (1,209 posts) but no grade scale on the listings | PDF, Guitar Pro, MIDI | Free; GAPS obtained permission to redistribute | abstract (site pages) |
| GAPS (Riley, Dixon et al., arXiv 2408.08653, 2024) | 300 classical guitar performances, 93 composers, tabs as MusicXML with string and fret, note-level MIDI alignments, YouTube audio; sources are ClassClef Guitar Pro files converted by MuseScore | MusicXML, MIDI | Free (licence unstated) | abstract |
| classtab.org (Wright) | ASCII classical guitar tabs, the source song2guitar used; the format gtrsnipe reads as written | ASCII tab | Free | listing (index fetched; no grades) |
| Ultimate Guitar difficulty field | Four levels (absolute beginner, beginner, intermediate, expert), chosen by the submitter, optional, rewarded with IQ points; formerly a community vote | Label per tab | Scraping terms unexamined | abstract (help centre) |

## 4. What this means for M03

1. **Ingredients, in the order the evidence supports them:** index-finger travel per onset
   (barre fret or lowest fretted fret), with the shift charged less when the inter-onset time
   is long; number of fingers down and stretch per onset (span, with scottvr's 2026-11-07
   reach rule); barre count; notes per second at tempo; chord-change rate; position-shift
   count; shape uncommonness (how rare the fingering is in a reference corpus, the TF-IDF
   idea); repetitiveness (how much of the tab is a repeat). Pitch-only descriptors (entropy,
   range) can ride along as a baseline to show they add little on guitar.
2. **Aggregate as a profile, not a total:** per-note or per-onset values summarised by mean,
   quadratic mean and maximum (the hardest bar), plus the tab's length separately. CMMR 2025
   and ISMIR 2023 both say length is not difficulty; Hori says the maximum is what players
   feel.
3. **Validate by rank correlation** against the RCM list (and Trinity or ABRSM for a second
   check), on the subset we can obtain as tabs or MIDI: ClassClef and classtab by title match,
   GAPS where it overlaps. Expect noise of about one level; report Spearman's rho and adjacent
   accuracy, as the literature does, and the per-ingredient correlations (Ariga's 0.55 is the
   number to beat for a single feature).
4. **No learning until the ingredients are measured.** The parked "learned weights" idea and
   RubricNet's shape are where it goes afterwards, if the hand-set weights leave rank
   correlation on the table.
5. **Side findings for the scorer** (not M03, noted for M06): time-scaled movement cost and a
   per-finger form cost (Hori), and the minimax objective as an alternative decode, which the
   parked "different objectives" entry already describes.

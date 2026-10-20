## LEGAL MEMORANDUM: THE IMPACT OF PHYSICAL INSTRUMENT COORDINATE AMBIGUITIES ON COPYRIGHT INFRINGEMENT CLAIMS

### 1. Introduction and Statement of the Representational Paradox

In intellectual property litigation involving music technology and digital media, a critical analytical fallacy arises from the failure to distinguish between physical motor instructions and copyrighted musical expression. While traditional copyright doctrine presumes that written sheet music directly embodies protected creative works, alphanumeric guitar tablature functions under a fundamentally different technical framework. Tablature does not directly encode musical pitches, harmonic relationships, or audible expressive structures; rather, it records spatial and mechanical coordinates directing a performer where to position their fingers on an instrument's fretboard. Because the translation of these physical motor coordinates into audible pitch structures depends entirely upon an external operational variable—specifically, the open-string tuning vector applied to the instrument—an isolated sequence of fretboard coordinates cannot be legally or mathematically presumed to embody a unique musical identity. Distinguishing physical execution instructions from protected auditory expression is of paramount strategic importance in infringement actions. Treating raw geometric coordinates as definitive representations of specific copyrighted compositions conflates unprotectable physical processes with protectable expression, misapplying the foundational statutory boundaries of copyright law.

Mathematically, a passage of alphanumeric guitar tablature is formalized as an ordered sequence of two-dimensional coordinate pairs:

$$T = \big((s_1,f_1),(s_2,f_2),\ldots,(s_n,f_n)\big)$$

where $s_i \in \{1, 2, \ldots, N\}$ represents the string index (for an N-string instrument) and $f_i \in \mathbb{Z}_{\ge 0}$ represents the fret position engaged at temporal step i. To convert any coordinate pair $(s, f)$ into an audible musical pitch $P$, the sequence must be processed through an external pitch decoding function. For a fretted instrument operating under twelve-tone equal temperament, the decoding equation is expressed as:

$$P = K(s) + f$$

where $P$ is the resulting musical pitch expressed in semitone units relative to a standard reference frequency (e.g., standard MIDI pitch numbers), $f$ is the non-negative integer fret index, and $K(s)$ represents the external operational key—specifically, a vector mapping each string index $s$ to its assigned open-string pitch value under tuning configuration $K$. The transformation of the entire coordinate sequence $T$ into a discrete pitch array $P = (P_1, P_2, \ldots, P_n)$ is explicitly governed by this vector mapping:

$$P_i = K(s_i) + f_i \quad \text{for } i \in \{1, 2, \ldots, n\}$$

Because pitch realization is strictly dependent on $K(s)$, altering the operational key $K$ systematically transforms the pitch array $P$, even when the physical coordinate sequence $T$ remains entirely invariant.

This mathematical dependency creates the phenomenon known as the tablature homograph. Let $T$ represent an invariant, static sequence of physical fretboard coordinates, and let $K_A$ and $K_B$ represent two distinct, non-identical open-string tuning vectors. Applying these independent decoding keys to the same physical coordinate sequence yields two distinct musical pitch outputs:

$$F(T, K_A) = W_A$$

$$F(T, K_B) = W_B$$

where $W_A$ and $W_B$ represent entirely independent, non-identical musical compositions. Under specific operational parameters, $W_A$ and $W_B$ resolve to recognizable, distinct excerpts from completely unrelated works. Consequently, a single, unadjusted sequence of mechanical instructions $T$ accurately describes two distinct musical compositions without requiring any copying, joint authorship, or shared creative heritage between the respective copyright owners.

The structural and functional distinctions between traditional notation and alphanumeric tablature are summarized in the comparative matrix below:

|Dimension	|Traditional Musical Notation	| Alphanumeric Tablature |
|----------------|------------------|--------------------|
|Primary Encoding Focus	|Inherent pitch, duration, and harmonic values	|Physical spatial coordinates $(s, f)$ on a fretboard|
|Operational Decoding Dependency	| Self-contained pitch definition; independent of apparatus mechanics	| Absolute dependency on external tuning key vector K(s)|
|Notation Stability	|Fixed score mapping directly to audible pitches	|Variable coordinate output dependent on operational key $(K)$|
|System Dependency	|Direct, human-readable musical representation|	Apparatus-dependent spatial execution instructions|

This mathematical reality establishes that physical fretboard coordinates lack an intrinsic, unique musical identity, creating an insuperable representational paradox when litigants attempt to assert exclusive copyright ownership over static instrument coordinate files.

### 2. The Cipher Paradox and Copyright Ownership Indeterminacy

Moving from basic mathematical definitions to information theory and cryptographic analysis, alphanumeric tablature functions identically to a keyed encoding system. In legal proceedings where copyright infringement is alleged based on raw coordinate matching, treating a static sequence of fretboard locations as self-evident proof of copying presents an insurmountable evidentiary hurdle. Without establishing the specific external decoding key intended by the author, an isolated coordinate string constitutes unkeyed data lacking fixed expressive meaning.

Under a polyalphabetic cipher analogy, guitar tablature operates as a keyed encoding framework wherein encoded symbols yield radically different plaintext outputs depending upon the operational key applied. While a fretted instrument neck is not a security cryptographic apparatus, nor is retuning an instrument formal encryption, both systems share a fundamental operational property: identical input symbols produce distinct, structured outputs when processed under different operational keys. Because the pitch sequence rendered by tablature is dictated by the open-string pitch values $K(s)$, an unkeyed coordinate sequence $T$ cannot resolve to a single musical composition in isolation.

This structural indeterminacy creates an acute ownership paradox in intellectual property litigation. Consider a scenario in which Composer $A$ holds a valid copyright in Composition $W_A$, which transcribes to coordinate sequence $T$ under tuning key $K_A$. Concurrently, Composer $B$ holds an independent copyright in Composition $W_B$, which maps to the exact same coordinate sequence $T$ when decoded using tuning key $K_B$. If both creators assert claims over the shared physical instructions $T$, significant legal impasses arise:

* Exclusive Ownership of Raw Coordinates: Neither Composer $A$ nor Composer $B$ can establish exclusive statutory ownership over the raw fretboard coordinates $T$, as the spatial grid sequence exists independently of either specific tuning key vector.
* Restriction of Independent Publication: Composer $A$ cannot suppress the publication or distribution of coordinate sequence $T$ by Composer $B$, as $T$ serves as an accurate physical representation of Composer $B$'s independent, non-infringing work $W_B$ under key $K_B$.
* Absence of Reciprocal Copying: The publication of $T$  by Composer $B$ under key $K_B$ does not constitute a reproduction of Composer $A$'s protected expression, despite the absolute physical identity of the recorded spatial sequence.

From a litigation strategy perspective, demonstrating a viable tablature homograph fundamentally reshapes the evidentiary burden of proof. In copyright infringement litigation, the plaintiff bears the initial burden of proving ownership of a valid copyright and actual copying of protected expression. When a plaintiff attempts to establish copying by demonstrating identical fretboard coordinate sequences, the defendant's introduction of a valid homograph shatters the presumption of identity. Demonstrating that $T$ decodes to an independent work $W_B$ under $K_B$ shifts the burden back to the plaintiff to affirmatively establish that the defendant copied the specific tuning vector $K_A$, contextual metadata, and intended expressive identity, rather than unprotectable motor coordinates.

The legal defense grounded in representational ambiguity possesses clear boundaries. This defense applies strictly to raw, abstract, and unadorned coordinate sequences. It does not retroactively immunize commercial files that are explicitly titled, arranged, labeled, and marketed as transcriptions of a specific protected composition. Where external metadata, titling, and commercial positioning establish an express intent to distribute a particular copyrighted work, straightforward infringement questions remain.

When unadorned fretboard coordinates are presented in court without external context or explicit tuning specifications, they exhibit three critical evidentiary deficiencies:

1. Absence of an Inherent Operational Decoding Key: The coordinate sequence lacks an embedded open-string pitch vector $K(s)$, rendering the mathematical determination of actual musical pitches impossible from the spatial text alone.
2. Indeterminacy of Unique Musical Identity: Because a single coordinate sequence $T$ can simultaneously decode to multiple unrelated compositions $(W_A, W_B)$, the raw spatial data fails to uniquely identify any single underlying protected musical work.
3. Insufficiency to Establish Infringing Expressive Intent: Static spatial coordinates do not, standing alone, prove an intent to copy protected musical expression, as the physical movements described are fully compatible with independent, non-infringing musical works under alternative operational keys.

These evidentiary gaps demonstrate that static spatial instructions cannot serve as standalone proof of copyright infringement, aligning directly with historical judicial precedents governing mechanical instructions.

### 3. Historical Precedent and Statutory Evolution of Mechanical Instructions

The legal classification of machine-readable and spatial performance instructions has a long statutory and judicial lineage. Understanding the historical division between expressive scores readable by humans and spatial instructions designed to operate a mechanical apparatus remains vital when evaluating modern digital notations like ASCII tablature.

In the landmark decision *White-Smith Music Publishing Co. v. Apollo Co., 209 U.S. 1 (1908)*, the Supreme Court addressed whether perforated paper piano rolls constituted statutory "copies" of copyrighted musical compositions. The Court held that physical piano rolls were not copies under the copyright laws then in effect. The Court's rationale turned on the fundamental distinction between traditional sheet music—a conventional notation system designed to communicate expressive musical ideas directly to human readers—and mechanical control mechanisms designed to physically actuate an apparatus. Although both media ultimately produced audible music, the mechanical spatial roll was classified as an operational component of a machine rather than a direct textual reproduction of protected expression.

TRADITIONAL MUSICAL NOTATION
[Written Notes] ---> [Musical Interpretation] ---> [Performance]

MECHANICAL INSTRUCTION SYSTEM
[Physical Coordinates] ---> [Configured Apparatus] ---> [Performance]

ASCII GUITAR TABLATURE
[Fret Coordinates] ---> [Configured Guitar Tuning] ---> [Performance]


ASCII guitar tablature mirrors the mechanical pipeline identified in White-Smith. Both piano rolls and alphanumeric tablatures record spatial positions designed to trigger physical events on an instrument. However, the guitar introduces a structural variable absent in standard player pianos: configurable open-string tuning. While a player piano maintains a fixed key-to-actuator alignment, a guitar permits independent adjustment of open-string pitch baselines $(K)$. Consequently, an identical sequence of ASCII fret coordinates can alter not merely the overall key, but the internal interval structures, harmonic progressions, and musical identities of the output.

Congress subsequently enacted statutory modifications to address the outcome in White-Smith. The Copyright Act of 1909 established statutory mechanical reproduction rights to capture recorded physical performances. Decades later, the Copyright Act of 1976 substantially expanded the statutory definition of "copies" under 17 U.S.C. § 101, defining them as material objects from which a work can be perceived, reproduced, or communicated either directly or "with the aid of a machine or device."

Crucially, however, modern statutory expansion under § 101 must be read in direct conjunction with 17 U.S.C. § 102(b). Section 102(b) explicitly codifies that:

---
>"In no case does copyright protection for an original work of authorship extend to any idea, procedure, process, system, method of operation, concept, principle, or discovery, regardless of the form in which it is described, explained, illustrated, or embodied in such work."
---

Fretboard coordinates (s_f, f_i) represent a pure method of operation and mechanical procedure for placing fingers on an instrument neck. While modern law treats machine-readable encodings as copies when they fixedly embody a per se recognizable work, § 102(b) precludes extending copyright protection to the underlying mechanical procedure itself.

What survives from White-Smith is its vital conceptual distinction between a musical work, its mechanical encoding, and the operating context necessary to render it. Modern copyright law recognizes mechanically encoded representations as copies only when fixed to a deterministic musical result; it does not transform an unkeyed, key-dependent spatial grid into a unique statutory work when isolated from operational decoding parameters. This legal principle moves the controversy from theoretical statutory analysis to empirical computational demonstration.

Further, is stands to reason from this, that as a set of coordinates, or even as a method or set of instructions, tablature falls more in the realm of patent protection than it does that of copyright, and obviously there is too much prior art for tablature encoding - even including its decoding key - to qualify for a patent either, but that is outside of the scope of this work.

### 4. Computational Evidence and Algorithmic Homograph Discovery

To establish whether tablature homographs represent practical legal realities rather than isolated academic anomalies, researchers developed the open-source computational musicology platform gtrsnipe. Moving beyond theoretical assumptions, gtrsnipe provides empirical verification of spatial ambiguities across large, standard musicological corpora, including the Essen Folk, Meertens Tune Collections, Nottingham, POP909, and Lakh datasets.

The algorithmic engine of gtrsnipe addresses the homograph search problem by examining how musical pitches map onto alternative physical fretboard layouts. Because a single pitch can often be executed across multiple string and fret combinations, and a single fret position can yield multiple pitches depending on tuning key $K$, the correspondence between sheet music and tablature is non-unique in both directions.

gtrsnipe models the guitar fretboard as a multi-stage, directed trellis graph. For a given musical pitch sequence, trellis nodes at stage i represent valid physical $(s_i, f_i)$ instantiations of pitch $P_i$. Directed edges between stage $i$ and stage $i+1$ represent physical transitions, assigned scalar weights based on ergonomic cost metrics (e.g., hand movement across frets, finger stretch span, string switching effort, and positional stability). The algorithm uses dynamic programming and Viterbi-style trellis path optimization to compute the globally optimal, minimum-cost physical path across the entire composition. Given two distinct compositions $W_A$ and $W_B$, the solver searches the combinatorial space of tuning keys $K_A$ and $K_B$ to determine whether a shared coordinate sequence $T$ satisfies $F(T, K_A)$ = $W_A$ and $F(T, K_B) = W_B$ subject to physical instrument tension constraints.

Empirical experiments executed across the referenced datasets (specifically experiments R03, R03b, R04, and R05) yielded vital quantitative findings:

* Tune Family Retrieval and Offset Measures (R03 & R03b Experiments): Experiment R03 evaluated whether counting distinct pitch offsets $(\delta = W_B - W_A)$, termed offset "richness," could retrieve related tune families across whole melodies. Findings revealed that offset richness alone is a weak predictor for whole-melody retrieval, gaining $\le$ 0.006 Mean Average Precision (MAP) over transposition-invariant Hamming distance baselines. However, experiment R03b demonstrated that when applied at the phrase and motif level under optimal dynamic time warping (DTW), offset measures yield a statistically significant performance gain (+0.009 to +0.010 MAP across all expert annotators). This proves that offset richness operates as a true structural measure of phrase-level melodic alignment.
* Prevalence in Short Passages (R04 Scan): Shared coordinate representations occur with high frequency in short musical phrases. Among sampled folk melodies sharing identical rhythmic structures, approximately one-third (33%) of 8-note phrase pairs fit across a standard six-string fretboard while producing completely unrelated auditory melodies under different tunings. This prevalence declines as passage length increases, falling to 8% for 12-note phrases and 3% for 16-note phrases.
* Physical String Tension Viability (R04 Physics): Homograph tuning keys do not require physically impossible instrument setups. Physical tension calculations reveal that 93% to 100% of sampled folk pairs (7–20 notes in length) can be physically executed on a standard acoustic or electric guitar anchored in standard tuning for Work A (with 23% to 60% requiring no string gauge modifications). For pop compositions in POP909/Lakh, 23% to 90% are physically playable under anchored conditions, rising to 93%–97% when both compositions permit custom tuning adjustments on a single instrument.
* Ergonomic and Playability Constraints (R04 Playability): While shared coordinate sequences are physically executable ("fingerable"), they are rarely ergonomically optimal. Out of 50 sampled homograph pairs, 49 yielded valid physical tabs; however, evaluation against gtrsnipe mapper cost metrics showed that only 19 pairs fell within 50 cost points per note of the original composition's native tab, 4 fell within 20 points, and 0 fell within 5 points. Shared tabs are physically achievable, though unoptimized fingerings reflect mechanical trade-offs.
* As-Written Fingering Ambiguity (R05 Experiment): Evaluating published, complete transcriptions ("as-written" fingerings) revealed that short 8-note passages exhibit hundreds of valid homograph partners. However, at phrase lengths of 24 and 32 notes, no unrelated-sounding melodies satisfy exact coordinate identity. The analysis proved that specific physical fingering choices, rather than raw melodic contours alone, dictate the existence of homograph partners.

The empirical research findings and their direct legal implications are synthesized in the table below:

Claim	Status	Empirical Evidence	Legal Implications
Short Passage Tab Sharing	Holds	33% of 8-note folk phrases share tabs; 8% at 12 notes; 3% at 16 notes (R04).	Substantial overlap in short passages prevents automated coordinate matching from proving copying.
String Tension Viability	Holds	93%–100% of folk pairs (7–20 notes) fit real instruments without breaking strings (R04).	Homograph defenses cannot be dismissed as physically impossible or theoretical fabrications.
Playability / Ergonomics	Mostly False	49/50 pairs have valid tabs, but 0/50 fall within 5 cost points of native ergonomics (R04).	Shared coordinates exist physically, though unoptimized fingerings reflect mechanical trade-offs.
As-Written Fingering Ambiguity	Tempered	Hundreds of partners at 8 notes; 0 unrelated partners at 24+ notes (R05).	Long, continuous transcriptions retain identity, but short excerpt claims remain ambiguous.

Because computing these Viterbi paths and string tension models requires executing dynamic programming across complete musical files, computational tools must process copyrighted transcriptions in their entirety, directly raising the statutory fair use defense.

### 5. Four-Factor Fair Use Analysis for Computational Musicology

The operation of computational musicology platforms such as gtrsnipe requires parsing digital transcriptions to evaluate physical playability, dynamic pathing, and representational homographs. Under 17 U.S.C. § 107, evaluating whether computational parsing of copyrighted tablature data constitutes non-infringing fair use requires balancing four statutory factors.

#### Factor 1: Purpose and Character of the Use

Automated parsing of tablature files by computational engines serves a transformative, highly research-oriented purpose. Rather than reproducing transcriptions for commercial distribution or entertainment, tools like gtrsnipe extract mathematical, spatial, and ergonomic data to evaluate structural representational properties. This functional, analytical operation aligns directly with judicial precedents affirming that intermediate copying necessary to perform functional data analysis constitutes fair use, as established in *Sega Enterprises Ltd. v. Accolade, Inc., 977 F.2d 1510 (9th Cir. 1992)*.

#### Factor 2: Nature of the Copyrighted Work

While underlying musical compositions represent creative expression sitting near the core of copyright protection, alphanumeric tablature files inherently incorporate non-protectable functional constraints under 17 U.S.C. § 102(b). Fretboard transcriptions reflect mechanical finger positions dictated by human hand anatomy, string scale lengths, and instrument physics. The functional, geometric mechanics embedded within tablature limit the scope of copyright monopolization over the underlying coordinate instructions.

#### Factor 3: Amount and Substantiality Used

Computational musicology engines frequently parse complete tablature files. Full-file ingestion is technically and algorithmically mandatory: evaluating global string tension viability and solving the Viterbi trellis path requires computing state transitions across the full temporal length of a piece. Selecting an optimal path through a multi-stage trellis cannot be accomplished by analyzing isolated fragments. Because full-file ingestion is strictly tailored to an analytical objective and does not redistribute expressive content to the public, full-file parsing is justified under Factor 3.

#### Factor 4: Effect Upon Potential Market

Command-line research platforms designed to discover homographs and compute physical playability metrics do not act as commercial market substitutes for authorized sheet music or commercial songbooks. A consumer seeking an expressive score for performance will not find utility in raw algorithmic reports detailing string tension metrics, Viterbi path costs, or multi-tuning offset transformations. Consequently, analytical research tools exert no market harm on the primary licensing markets for consumer music scores.

To maintain strategic clarity in intellectual property litigation, defense counsel must rigorously distinguish between the structural defense and the statutory fair use defense:

* Representational Ambiguity Argument: Asserts that raw coordinate data $T$ lacks a single, inherent musical identity prior to applying an external decoding key $K$, meaning the media itself does not uniquely represent a single protected work under 17 U.S.C. § 102(b).
* Fair Use Defense (17 U.S.C. § 107): Asserts that even where underlying source material unambiguously encodes a specific copyrighted composition, analyzing and processing that data for distinct computational, research, or educational purposes is statutorily permissive.

Differentiating between these two legal concepts ensures that structural properties of instrument representations are not confused with statutory exceptions for computational research.

#### 6. Conclusion and Legal Prayer for Relief

The legal controversy surrounding digital instrument transcriptions carries deep historical roots, notably evidenced by enforcement actions and cease-and-desist campaigns that led to the shutdown of prominent community repositories such as the On-Line Guitar Archive (OLGA). Throughout the 1990s and 2000s, publishing entities and licensing organizations (such as the Harry Fox Agency) issued blanket takedown notices premised on an oversimplified, legally flawed equation: asserting that physical coordinate transcriptions are per se direct reproductions of copyrighted musical compositions.

While that enforcement logic holds true for full-length transcriptions accompanied by explicit metadata and standard tuning references, rigorous computational analysis demonstrates that the underlying representational mechanics are far more complex. Spatial coordinates record motor positions, not acoustic pitches; pitch realization requires an external tuning key vector $K(s)$; and identical coordinate sequences can simultaneously represent multiple unrelated compositions under physically viable instrument settings.

Where static spatial instructions are isolated from external contextual metadata, no intrinsic mathematical property establishes which underlying musical composition was intended. Grounding copyright infringement actions solely on raw physical coordinate identity ignores the mathematical and physical realities of fretted stringed instruments.

**PRAYER FOR RELIEF**

Premised upon the mathematical proofs, empirical evidence, and statutory analysis set forth herein, Defendant respectfully requests that this Court grant the following formal relief pursuant to federal equity practice and the Declaratory Judgment Act, 28 U.S.C. § 2201:

1. Declaratory Judgment of Mathematical Homographs: Enter a formal judicial declaration recognizing the mathematical existence of tablature homographs, establishing that an invariant sequence of fretboard coordinates T decodes to multiple independent musical compositions under distinct open-string tuning vectors K.
2. Declaratory Judgment of Non-Uniqueness under 17 U.S.C. § 102(b): Hold that unkeyed physical instrument spatial coordinates constitute unprotectable motor procedures under 17 U.S.C. § 102(b) and do not exhibit an inherent, one-to-one identity with protected musical expression in the absence of explicit operational decoding parameters.
3. Order Denying Copyright Monopolization of Fretboard Geometry: Refuse to extend copyright protection or monopoly control over abstract geometric fretboard coordinate relationships where such spatial configurations merely describe physical motor actions on an instrument neck.
4. Order Affirming Protection for Computational Musicology Research: Order that the automated parsing, dynamic programming trellis path analysis, and structural evaluation of instrument coordinates by computational musicology platforms constitutes non-infringing fair use under 17 U.S.C. § 107.
5. Judicial Notice of Repository History and Metadata Context: Take formal judicial notice of the contextual history of community tablature archives, holding that raw, unadorned mechanical coordinate matching is legally insufficient to establish willful infringement without independent proof of intended copying of protected expression and key metadata.

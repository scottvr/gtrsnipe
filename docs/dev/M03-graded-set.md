# M03: the graded set (brief for scottvr, 2026-11-07)

**Goal.** A set of classical guitar pieces with an expert grade and a tab we can read, to
validate the difficulty measure by rank correlation. The grades come from the RCM Classical
Guitar Syllabus (2018 edition), 429 pieces across Preparatory and Levels 1 to 8; the tabs have
to come from elsewhere.

**The list.** `runs/m03-graded-set-2026-11-07/rcm-2018-list.csv` (level, section, title,
composer, page in the RCM book). It is the Da Capo Music transcription of the RCM books, so
expect the odd typo. The composers with the most entries, and the likeliest to exist as free
tabs: Sor, Carulli, Carcassi, Aguado, Giuliani, Sagreras, Diabelli, Tárrega, Coste, Blum.
The modern Canadian and contemporary composers (Bell, McFadden, Kraft, Gagnon, Jackman) are
unlikely to exist anywhere free and can be skipped.

**What we need, per piece, in order of preference.**
1. **An ASCII tab** (classtab.org `.txt`): it carries the fingering *as written*, which is what
   a difficulty measure of a tab should see; gtrsnipe reads ASCII tabs natively (R05 used
   its own). classtab's Sor, Carulli, Carcassi, Aguado, Giuliani and Sagreras collections are
   large, and the studies are mostly there under their opus numbers (e.g. "Sor op. 60 no. 1",
   "Carcassi op. 60 no. 7", "Aguado lesson N", "Sagreras lesson N").
2. **A Guitar Pro file and its MIDI** (classclef.com): the Guitar Pro file has the fingering,
   but gtrsnipe cannot read it yet (a `.gp` reader is parked); the MIDI it can read, and the
   mapper would then supply a fingering, which is a weaker test (the measure would be scoring
   our fingering, not the editor's). Take both when they are there; the Guitar Pro file is
   insurance for when a reader exists.
3. **PDF only**: not useful (no OMR), skip.

**Where to put them.** `/Volumes/LaCie/data/midi/graded/rcm/` with one folder per level
(`P`, `1` … `8`), the file named `<composer-surname>_<short-title>.<ext>` (e.g.
`sor_op60-01.txt`, `carcassi_op60-07.gp5`, `carcassi_op60-07.mid`), and a `manifest.csv`
beside them: `level,title,composer,file,source_url,notes`. A copy of the source page URL per
file is what makes the set citable; the notes column is for "tab says drop D", "two versions
on the site, took the first", and so on.

**How many.** Any coverage helps: even 40 pieces spread over the levels give a rank
correlation. Aim for 10 or more per level if the sites allow; Preparatory and Level 1 will be
the hardest to find (modern pedagogical pieces).

**Terms.** classtab.org is Wright's free archive, used by song2guitar (Ariga et al. 2017).
ClassClef gave the GAPS authors permission to redistribute; its own terms are unexamined, so
the set stays local, as R14's third-party tabs do.

**Other lists, if the RCM one runs dry:** Trinity classical guitar (Initial to Grade 8) and
ABRSM (Grades 1 to 8) publish their lists; Delcamp's free editions are organised in grades 1
to 12 but are PDFs.

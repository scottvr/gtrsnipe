"""Figure: how often two phrases from different songs can share one tab (R04).

The real version of collision_plot_template.py (same styling), drawn from the
JSON that `gtrsnipe-research scan ... --physics-sample N --json FILE` writes.
For each phrase length (notes), among same-rhythm pairs from different works:

  eligible              richness 2-6: the offsets fit six strings (free tunings)
  unrelated-sounding    ... with more distinct pitch pairs than strings, no single
                        transposition explaining half the notes, contour agreement
                        <= 0.6, and no mechanical figure (arpeggio, ostinato...)
  playable              ... times the share of sampled pairs the full solver
                        places on a real guitar: one tab of A in STANDARD, the
                        other song a retune of it, string physics on
  no restring           ... the same without swapping any string's gauge

Run:  python docs/dev/r04_plot.py scan.json [more.json ...] [--out fig.png] [--min-sample 10]
      (several files are merged by length -- e.g. one window-length scan each)
"""
import json
import sys

import matplotlib.pyplot as plt


def curves(data, min_sample=10, max_len=32):
    xs, elig, dist, play, norestr = [], [], [], [], []
    for L, s in sorted(data["stats"].items(), key=lambda kv: int(kv[0])):
        L = int(L)
        if L > max_len or not s["pairs"]:
            continue
        xs.append(L)
        elig.append(100 * s["eligible"] / s["pairs"])
        d = 100 * s["unrelated"] / s["pairs"]
        dist.append(d)
        ph = data.get("physics", {}).get(str(L))
        if ph and ph["sampled"] >= min_sample:
            play.append((L, d * ph["anchored"] / ph["sampled"]))
            norestr.append((L, d * ph["anchored_no_regauge"] / ph["sampled"]))
    return xs, elig, dist, play, norestr


def load(paths):
    """Merge scans: per-length stats and physics samples add up."""
    data = {"stats": {}, "physics": {}, "corpora": []}
    for p in paths:
        d = json.load(open(p))
        for c in d.get("corpora", []):
            if c not in data["corpora"]:
                data["corpora"].append(c)
        for part in ("stats", "physics"):
            for L, v in d.get(part, {}).items():
                acc = data[part].setdefault(L, {})
                for k, x in v.items():
                    if isinstance(x, (int, float)):
                        acc[k] = acc.get(k, 0) + x
    return data


def _opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    skip = {sys.argv.index(o) + 1 for o in ("--out", "--min-sample") if o in sys.argv}
    paths = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and i not in skip]
    min_sample = int(_opt("--min-sample", 10))
    out = _opt("--out")
    data = load(paths)
    xs, elig, dist, play, norestr = curves(data, min_sample)

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 11, 'axes.labelsize': 12,
                         'axes.titlesize': 13, 'xtick.labelsize': 10, 'ytick.labelsize': 10})
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot(xs, elig, label='Offsets fit six strings (free tunings)', color='#1f77b4', linewidth=2.5)
    ax.plot(xs, dist, label='... and the passages sound unrelated', color='#ff7f0e',
            linewidth=2.5, linestyle='--')
    if play:
        ax.plot(*zip(*play), label='... and playable: A in STANDARD, B a retune',
                color='#2ca02c', linewidth=2, marker='o', markersize=4)
        ax.plot(*zip(*norestr), label='... with no string re-gauged', color='#d62728',
                linewidth=2, linestyle=':', marker='s', markersize=4)
    ax.set_title('Same-rhythm passages from different songs that share a tab', pad=15,
                 weight='bold')
    ax.set_xlabel('Passage length (notes)', labelpad=10)
    ax.set_ylabel('Share of same-rhythm pairs (%)', labelpad=10)
    ax.set_xlim(min(xs), max(xs))
    ax.set_ylim(-3, 103)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='none')
    corpora = " + ".join(data.get("corpora", []))
    ax.text(0.01, -0.16, f"Corpora: {corpora}. Physics curves from random samples "
            f"(>= {min_sample} pairs per length).", transform=ax.transAxes, fontsize=8, color='#555')
    plt.tight_layout()
    if out:
        plt.savefig(out, bbox_inches='tight', dpi=300)
    else:
        plt.show()


if __name__ == "__main__":
    main()

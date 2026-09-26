"""Figure template: how often do phrases in a corpus share a tab?

Contributed by Gemini via scottvr. The curves are ILLUSTRATIVE -- two hand-picked
logistic functions, not data. R04 (the corpus homograph scan, see BACKLOG.md) is
meant to produce the real numbers; keep the styling and swap the curves for
measured ones.

Run:  python docs/dev/collision_plot_template.py [out.png]
      (shows the figure, or saves it at 300 dpi when given a path)
"""
import sys

import matplotlib.pyplot as plt
import numpy as np

# Set clean, publication-ready style parameters
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
})

# 1. Generate search space dimensions (number of tunings evaluated)
x = np.linspace(1, 50, 200)

# 2. Simulate collision curves using logistic growth functions
# Short phrases saturate rapidly due to fewer constraints
y_short = 100 / (1 + 15 * np.exp(-0.25 * x))
# Standard phrases scale more deliberately as structural entropy increases
y_standard = 100 / (1 + 80 * np.exp(-0.15 * x))

# 3. Initialize high-resolution plot
fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

# 4. Plot curves with distinct visual treatments for black/white or color printing
ax.plot(x, y_short, label='Short Phrases (4–8 notes)', color='#1f77b4', linewidth=2.5)
ax.plot(x, y_standard, label='Standard Phrases (12–16 notes)', color='#ff7f0e', linewidth=2.5, linestyle='--')

# 5. Labeling and structural styling
ax.set_title('Homographic Intersection Density Across a Melody Corpus', pad=15, weight='bold')
ax.set_xlabel('Number of Alternate Tunings Evaluated ($N$)', labelpad=10)
ax.set_ylabel('Probability of Finding Overlapping Coordinates (%)', labelpad=10)

# Bound the axes logically to the data limits
ax.set_xlim(0, 50)
ax.set_ylim(-5, 105)

# Format the grid lines and remove unnecessary border boxes
ax.grid(True, linestyle=':', alpha=0.6)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Render clean legend bounding box
ax.legend(loc='lower right', frameon=True, facecolor='white', edgecolor='none')

# Output rendering optimizations
plt.tight_layout()

if len(sys.argv) > 1:
    plt.savefig(sys.argv[1], bbox_inches='tight', dpi=300)
else:
    plt.show()

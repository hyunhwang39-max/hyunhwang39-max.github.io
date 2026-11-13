"""Reproduce the portfolio's illustrative charts. All figures are fictional.

Run: pip install matplotlib
     python scripts/plot_margins.py
Outputs: assets/margin-analysis.svg and assets/margin-analysis.png
"""
from pathlib import Path
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / '.plot-deps').exists():
    sys.path.insert(0, str(ROOT / '.plot-deps'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

MARKETS = ['Korea', 'Japan', 'Southeast Asia']
SALES = [500, 300, 200]
COSTS = [275, 195, 150]
SAVING = 3  # Assumed packaging cost reduction; KRW million.
MARGINS = [(s-c)/s*100 for s, c in zip(SALES, COSTS)]
TOTAL_SALES = sum(SALES)
PROFIT = TOTAL_SALES - sum(COSTS)
AFTER = PROFIT + SAVING
BASE_MARGIN = PROFIT / TOTAL_SALES * 100
NEW_MARGIN = AFTER / TOTAL_SALES * 100
assert round(BASE_MARGIN, 1) == 38.0 and round(NEW_MARGIN, 1) == 38.3

INK, MUTED, GOLD, LINE = '#242424', '#66635d', '#a28a58', '#e5e1d9'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'text.color': INK, 'axes.labelcolor': MUTED,
                     'xtick.color': MUTED, 'ytick.color': INK,
                     'svg.fonttype': 'path', 'svg.hashsalt': 'margin-demo'})
fig, axes = plt.subplots(2, 1, figsize=(10, 9.2))
fig.set_facecolor('#fcfbf8')
fig.subplots_adjust(left=.19, right=.90, top=.79, bottom=.12, hspace=.98)
fig.text(.07, .955, 'PROJECT NOTE  /  01', fontsize=10, color=GOLD, weight='bold')
fig.text(.07, .908, 'Where can margins improve?', fontsize=24, weight='bold')
fig.text(.07, .87, 'A market comparison and one packaging-cost scenario.', fontsize=11, color=MUTED)

ax = axes[0]
ax.set_facecolor('#fcfbf8')
ax.set_title('01   Compare market profitability', loc='left', fontsize=13, weight='bold', pad=22)
ax.barh(MARKETS, MARGINS, height=.43, color=[INK, '#96948e', GOLD], zorder=3)
ax.invert_yaxis()
ax.set_xlim(0, 50)
ax.set_xticks([0, 10, 20, 30, 40, 50])
ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
ax.grid(axis='x', color=LINE, linewidth=.6, zorder=0)
ax.set_xlabel('Gross margin', fontsize=10, labelpad=9)
for i, value in enumerate(MARGINS):
    ax.text(value+1, i, f'{value:.1f}%', va='center', fontsize=12, weight='bold', zorder=5,
            bbox={'facecolor':'#fcfbf8', 'edgecolor':'none', 'pad':2})
ax.axvline(BASE_MARGIN, color=GOLD, linestyle=(0, (3, 3)), linewidth=1)
ax.text(BASE_MARGIN, 1.04, 'Portfolio 38.0%', transform=ax.get_xaxis_transform(),
        color='#806a40', fontsize=9, ha='center')

ax = axes[1]
ax.set_facecolor('#fcfbf8')
ax.set_title('02   Translate a cost action into profit', loc='left', fontsize=13, weight='bold', pad=28)
ax.bar([0, 2], [PROFIT, AFTER], width=.52, color=[INK, GOLD], zorder=3)
ax.bar(1, SAVING, bottom=PROFIT, width=.52, color=GOLD, zorder=3)
ax.plot([.26, .74], [PROFIT, PROFIT], color='#aaa69e', linestyle='--', linewidth=1)
ax.plot([1.26, 1.74], [AFTER, AFTER], color='#aaa69e', linestyle='--', linewidth=1)
ax.text(0, PROFIT+14, f'{PROFIT}\n{BASE_MARGIN:.1f}% margin', ha='center', va='bottom', fontsize=11)
ax.text(2, AFTER+14, f'{AFTER}\n{NEW_MARGIN:.1f}% margin', ha='center', va='bottom', fontsize=11)
ax.annotate('+3', xy=(1, PROFIT+SAVING/2), xytext=(1, 270), ha='center', fontsize=15,
            color='#806a40', weight='bold', arrowprops={'arrowstyle':'-', 'color':GOLD})
ax.set_ylim(0, 490)
ax.set_yticks([0, 100, 200, 300, 400])
ax.set_xticks([0, 1, 2], ['Baseline', 'Packaging saving', 'Scenario'])
ax.set_ylabel('Gross profit / KRW million', fontsize=10, labelpad=12)
ax.grid(axis='y', color=LINE, linewidth=.6, zorder=0)
for ax in axes:
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='both', length=0, pad=9)
fig.text(.07, .055, 'ILLUSTRATIVE DATA ONLY  |  Not an achieved business result.', fontsize=9, color=MUTED)
fig.text(.07, .03, 'Sales fixed at KRW 1,000m. Other costs unchanged. One-off transition costs excluded.', fontsize=9, color=MUTED)
(ROOT / 'assets').mkdir(exist_ok=True)
fig.savefig(ROOT / 'assets/margin-analysis.svg', facecolor=fig.get_facecolor(), metadata={'Date': None})
fig.savefig(ROOT / 'assets/margin-analysis.png', dpi=160, facecolor=fig.get_facecolor())
plt.close(fig)
print(f'Generated charts: margins={MARGINS}, profit={PROFIT}->{AFTER}, improvement={NEW_MARGIN-BASE_MARGIN:.1f}pp')
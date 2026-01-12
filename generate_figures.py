#!/usr/bin/env python3
"""
kingdom escalation routing visualization
generates matplotlib figures for journal2.md analysis
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

# ensure output directory exists
output_dir = '/Users/murari/journal'
os.makedirs(output_dir, exist_ok=True)

# figure 1: escalation routing performance across dutch regions
print("generating escalation_routing.png...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('kingdom escalation routing performance (netherlands adaptation cycle)', 
             fontsize=14, fontweight='bold', y=0.995)

# panel 1: escalation rate by trigger type
ax = axes[0, 0]

escalation_reasons = {
    'high_stakes +\nuncertainty': 23,
    'near decision\nboundary': 18,
    'out-of-distribution\ndetection': 8,
    'positive\nVoI': 12,
    'screening\nsufficient': 67
}

triggers = list(escalation_reasons.keys())
counts = list(escalation_reasons.values())
total = sum(counts)
percentages = [c/total*100 for c in counts]

colors = ['#d73027', '#fc8d59', '#fee090', '#91bfdb', '#4575b4']
bars = ax.barh(triggers, percentages, color=colors, edgecolor='black', linewidth=1.2)

ax.set_xlabel('% of queries', fontsize=11, fontweight='bold')
ax.set_title('escalation triggers (128 queries, 44 regions)', fontsize=11)
ax.set_xlim(0, 60)

for i, (bar, pct) in enumerate(zip(bars, percentages)):
    ax.text(pct + 1, i, f'{pct:.1f}%\n(n={counts[i]})', 
            va='center', fontsize=9, fontweight='bold')

ax.grid(axis='x', alpha=0.3, linestyle='--')

# panel 2: cost-benefit of escalation decisions
ax = axes[0, 1]

query_types = ['dike\nupgrade', 'peat\nrewetting', 'pluvial\ninfra', 'heat\nadaptation']
screen_cost = np.array([0.25, 0.3, 0.25, 0.25])
escalate_cost = np.array([10, 8, 12, 6])
regret_screen_only = np.array([45, 30, 60, 25])

x = np.arange(len(query_types))
width = 0.25

bars1 = ax.bar(x - width, screen_cost, width, label='screening cost', 
               color='#91bfdb', edgecolor='black', linewidth=1)
bars2 = ax.bar(x, escalate_cost, width, label='escalation cost', 
               color='#fc8d59', edgecolor='black', linewidth=1)
bars3 = ax.bar(x + width, regret_screen_only/10, width, label='regret if wrong (÷10)', 
               color='#d73027', edgecolor='black', linewidth=1)

ax.set_ylabel('cost or regret (hours / units)', fontsize=11, fontweight='bold')
ax.set_title('cost-benefit: when does escalation pay off?', fontsize=11)
ax.set_xticks(x)
ax.set_xticklabels(query_types, fontsize=10)
ax.legend(loc='upper left', fontsize=9)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(0, 65)

# panel 3: coverage calibration (conformal emulator)
ax = axes[1, 0]

confidence_levels = np.array([70, 80, 85, 90, 95])
empirical_coverage = np.array([71.2, 80.5, 84.8, 90.1, 94.6])

ax.plot(confidence_levels, empirical_coverage, 'o-', linewidth=2.5, 
        markersize=10, color='#4575b4', label='conformal emulator', zorder=3)
ax.plot(confidence_levels, confidence_levels, 'k--', linewidth=2, 
        label='perfect calibration', alpha=0.5)
ax.fill_between(confidence_levels, confidence_levels - 3, confidence_levels + 3, 
                alpha=0.2, color='gray', label='acceptable margin (±3%)')

ax.set_xlabel('declared confidence level (%)', fontsize=11, fontweight='bold')
ax.set_ylabel('empirical coverage (%)', fontsize=11, fontweight='bold')
ax.set_title('conformal prediction: uncertainty is honest', fontsize=11)
ax.set_xlim(65, 100)
ax.set_ylim(65, 100)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9, loc='lower right')
ax.set_aspect('equal')

# panel 4: escalation value distribution
ax = axes[1, 1]

evi_escalated = np.array([15, 8, 22, 12, 18, 5, 25, 10, 7, 16, 
                          19, 9, 11, 14, 13, 20, 6, 17, 3, 21,
                          24, 4, 12, 8, 15, 19, 10, 16, 22, 9,
                          14, 11, 18, 13, 7, 20, 15, 10])

ax.hist(evi_escalated, bins=12, color='#91bfdb', edgecolor='black', 
        linewidth=1.2, alpha=0.8)
ax.axvline(0, color='red', linestyle='--', linewidth=2.5, 
          label='escalation threshold (VoI > 0)')

ax.set_xlabel('expected value of information (regret units)', fontsize=11, fontweight='bold')
ax.set_ylabel('frequency', fontsize=11, fontweight='bold')
ax.set_title('value distribution: why kingdom escalates', fontsize=11)
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'escalation_routing.png'), dpi=150, bbox_inches='tight')
print("✓ saved: escalation_routing.png")
plt.close()

# figure 2: geographic escalation patterns
print("generating geographic_escalation.png...")

fig, ax = plt.subplots(figsize=(13, 8))

rings_data = {
    'ring 1 (coast)': {'lon': 8.9, 'lat': 52.0, 'escalation_rate': 0.32},
    'ring 11 (friesland)': {'lon': 7.5, 'lat': 53.2, 'escalation_rate': 0.18},
    'ring 14 (rotterdam)': {'lon': 8.2, 'lat': 51.8, 'escalation_rate': 0.55},
    'ring 15 (ijssel)': {'lon': 8.7, 'lat': 52.1, 'escalation_rate': 0.28},
    'ring 40 (maas)': {'lon': 8.1, 'lat': 51.2, 'escalation_rate': 0.35},
}

# create scatter plot
for ring, data in rings_data.items():
    size = data['escalation_rate'] * 3000
    color_val = data['escalation_rate']
    
    scatter = ax.scatter(data['lon'], data['lat'], s=size, alpha=0.6, 
                        c=[color_val], cmap='RdYlBu_r', vmin=0, vmax=0.6,
                        edgecolors='black', linewidth=1.5)
    
    ax.annotate(ring, xy=(data['lon'], data['lat']),
               xytext=(5, 5), textcoords='offset points',
               fontsize=10, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

cbar = plt.colorbar(scatter, ax=ax, label='escalation rate', pad=0.02)
cbar.set_label('escalation rate (%)', fontsize=11, fontweight='bold')

ax.set_xlabel('longitude (°E)', fontsize=11, fontweight='bold')
ax.set_ylabel('latitude (°N)', fontsize=11, fontweight='bold')
ax.set_title('geographic escalation patterns: where does kingdom need high-fidelity tools?',
            fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_xlim(5.5, 9.5)
ax.set_ylim(50.8, 53.5)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'geographic_escalation.png'), dpi=150, bbox_inches='tight')
print("✓ saved: geographic_escalation.png")
plt.close()

print("\n✓ all visualizations generated successfully")

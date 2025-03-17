import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# Data
categories = [
    "Governo - Presidente", "Governo", "Camera - Presidente", "Camera", "Senato - Presidente",
    "Senato", "Ambasciate", "Sindaci", "Sindaci >100k abitanti", "Giunta comune",
    "Consiglio comune", "Presidenza Regione", "Giunta Regione", "Consiglio Regione",
    "Società controllate MEF - CEO", "Società quotate - CEO", "Società quotate - Presidente",
    "Gruppi bancari - CEO", "Gruppi Tech - CEO", "Quotidiani - Direzione", "TG - Direzione",
    "Agenzie di stampa - Direzione", "Atenei - Rettore o rettrice", "Enti di ricerca - Direttore generale",
    "Autorità indipendenti - Presidente"
]

male_counts = np.array([0, 18, 1, 267, 1, 129, 153, 6578, 35, 14842, 60451, 18, 97, 510, 34, 48, 41, 9, 18, 47, 10, 4, 0, 11, 8])
female_counts = np.array([1, 6, 0, 132, 0, 75, 24, 1194, 9, 10574, 32447, 2, 37, 172, 6, 2, 9, 1, 1, 3, 0, 3, 0, 3, 3])

# Normalize data for color intensity
normalized_male = male_counts / (male_counts + female_counts + 1e-5)
normalized_female = female_counts / (male_counts + female_counts + 1e-5)

# Create a matrix where each column represents male and female values
matrix = np.column_stack((normalized_male, normalized_female))

# Define custom colormap (white to pink)
custom_cmap_reversed = LinearSegmentedColormap.from_list("custom_white_pink", ["#ffffff", "#ff006d"])

# Create a properly formatted annotation array
annotations = np.column_stack((male_counts, female_counts)).astype(str)

# Compute the aspect ratio
base_height = 10  # Reference height
base_width = (558 / 617) * base_height  # Compute width proportionally

# Generate the heatmap with fixed aspect ratio
fig, ax = plt.subplots(figsize=(base_width + 2, base_height))  # Add extra width
sns.heatmap(matrix, annot=annotations, fmt="s", cmap=custom_cmap_reversed,
            linewidths=0.5, linecolor="#333", cbar=False,
            xticklabels=False, yticklabels=categories, ax=ax,
            annot_kws={"fontsize": 12, "fontweight": "bold"})  

# Move x-ticks to the top
ax.xaxis.tick_top()
ax.xaxis.set_label_position('top')
ax.set_xticks([0.5, 1.5])
ax.set_xticklabels(["M", "F"], fontsize=14, fontweight="bold")
ax.set_yticklabels(categories, ha="left", va="center", fontsize=11, fontweight="bold")
ax.tick_params(axis="x", which="both", length=0)  
ax.yaxis.set_tick_params(pad=240)  
ax.tick_params(axis="y", which="both", length=0)  

# Adjust layout to avoid label overlap
plt.subplots_adjust(left=0.5)  

# Save outputs
png_path = "./tabella.png"
svg_path = "./tabella.svg"

plt.savefig(png_path, dpi=300, transparent=True)
plt.savefig(svg_path, format="svg")

# Show the plot
plt.show()

# Return file paths
png_path, svg_path

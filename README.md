# NFHS-5 Indian States Health Indicator Analysis & Interactive Dashboard

This project provides a complete pipeline to download, clean, structure, analyze, and visualize state-level public health indicators from the National Family Health Survey (NFHS-5, 2019-21) in India. It includes correlation analysis, regional clustering visualization, and an interactive geographic Folium dashboard.

## Features

- **Phase 1: Automated Data Setup & Pipeline**
  - Downloads the official state-level CSV dataset and caches it locally.
  - Pivots the long-format survey data into a clean state-by-indicator table.
  - Handles non-numeric markers (e.g. `-` and `*`) using numeric coercion.
  - Maps state name spelling to align with modern GeoJSON boundaries (e.g. resolving NCT Delhi, Dadra & Nagar Haveli, and Jammu & Kashmir).
  - Engineers a `Gender_Obesity_Gap` column ($\text{Obesity}_{\text{Female}} - \text{Obesity}_{\text{Male}}$).

- **Phase 2: Exploratory Data Analysis & Plots**
  - Computes Pearson correlation coefficients to evaluate the **Double Burden of Malnutrition** (childhood anaemia vs. adult obesity).
  - Generates a grouped bar chart (`hypertension_bar.png`) highlighting the top 10 states with the highest rates of hypertension in men versus women.
  - Generates a scatter plot (`correlation_scatter.png`) of women's anaemia vs. obesity, color-coded by region, with state abbreviations.

- **Phase 3: Interactive Geographic Map**
  - Uses Folium to render an interactive map of India centered at coordinate `[20.5937, 78.9629]`.
  - Binds the cleaned dataset to state boundaries in a GeoJSON choropleth layer representing the prevalence of adult obesity.
  - Places custom markers on all 36 state capitals with beautifully formatted HTML tooltips highlighting State Name, Obesity Rate (%), High Blood Sugar Rate (%), and Anaemia Rate (%).

---

## Directory Structure

```
sic_handson/
├── analyze_health.py           # Main Python analysis & dashboard generation script
├── README.md                   # Project documentation (this file)
├── NFHS-5-States.csv           # Cached CSV dataset from Pratap Vardhan's repository (downloaded automatically)
├── india_states.geojson        # Cached India GeoJSON boundary file (downloaded automatically)
├── hypertension_bar.png        # Bar chart comparing hypertension in men vs women (generated automatically)
├── correlation_scatter.png     # Scatter plot of women's anaemia vs obesity (generated automatically)
└── india_health_dashboard.html # Interactive Folium map dashboard (generated automatically)
```

---

## Getting Started

### Prerequisites

You need Python 3.8+ installed on your system. 

Install the required dependencies using pip:

```bash
pip install pandas matplotlib folium requests numpy
```

### Running the Analysis

Run the main analysis script from your terminal:

```bash
python analyze_health.py
```

Running the script will:
1. Download raw data files (`NFHS-5-States.csv` and `india_states.geojson`) if they do not exist locally.
2. Clean, filter, and pivot the dataset.
3. Compute and print Pearson correlation values.
4. Save the plots (`hypertension_bar.png` and `correlation_scatter.png`) to the workspace directory.
5. Create and save the interactive map dashboard (`india_health_dashboard.html`).

---

## Summary of Findings

- **Malnutrition Hypothesis**: The correlation coefficient between childhood anaemia and average adult obesity is **-0.2662**. The weak-to-moderate negative correlation indicates a geographic split between states struggling with undernutrition (high childhood anaemia) and states struggling with overnutrition (high adult obesity).
- **Hypertension by Gender**: Across the top 10 states with the highest rates of hypertension (led by Sikkim and Punjab), men consistently display higher prevalence rates than women.
- **Regional Clustering**: The scatter plot highlights distinct regional clusters. Southern states and Islands show high obesity with lower-to-moderate anaemia, while Eastern states (e.g. Bihar, Jharkhand, West Bengal) present high anaemia rates alongside low-to-moderate obesity.

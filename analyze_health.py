import os
import sys
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import folium
from folium import Choropleth, CircleMarker, Popup

# Setup UTF-8 console output for Windows environment
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Define raw data URLs
CSV_URL = "https://raw.githubusercontent.com/pratapvardhan/NFHS-5/master/NFHS-5-States.csv"
GEOJSON_URL = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"

# Local file caching
CSV_PATH = "NFHS-5-States.csv"
GEOJSON_PATH = "india_states.geojson"

print("--- PHASE 1: Data Setup and Aggregation ---")

# Step 1: Download the official state-wise indicator dataset
if not os.path.exists(CSV_PATH):
    print(f"Downloading dataset from {CSV_URL}...")
    r = requests.get(CSV_URL)
    with open(CSV_PATH, 'wb') as f:
        f.write(r.content)
    print("CSV Download complete.")
else:
    print("Using cached CSV file.")

if not os.path.exists(GEOJSON_PATH):
    print(f"Downloading GeoJSON from {GEOJSON_URL}...")
    r = requests.get(GEOJSON_URL)
    with open(GEOJSON_PATH, 'wb') as f:
        f.write(r.content)
    print("GeoJSON Download complete.")
else:
    print("Using cached GeoJSON file.")

# Step 2: Load the CSV file into a Pandas DataFrame
df = pd.read_csv(CSV_PATH)
print(f"Original dataset shape: {df.shape}")

# Define key indicators mapping using list item prefix
indicator_mapping = {
    "88.": "Obesity_Women",
    "89.": "Obesity_Men",
    "92.": "Anaemia_Children",
    "95.": "Anaemia_Women",
    "101.": "Blood_Sugar_Women",
    "104.": "Blood_Sugar_Men",
    "107.": "Hypertension_Women",
    "110.": "Hypertension_Men"
}

# Clean indicators and label them
df['indicator_clean'] = None
for prefix, col_name in indicator_mapping.items():
    mask = df['indicator'].str.strip().str.startswith(prefix)
    df.loc[mask, 'indicator_clean'] = col_name

# Filter for the relevant indicators
df_filtered = df.dropna(subset=['indicator_clean'])
print(f"Filtered rows count: {df_filtered.shape[0]}")

# Pivot the DataFrame to have states as rows and indicators as columns
df_pivot = df_filtered.pivot(index='state', columns='indicator_clean', values='nfhs5_total')

# Step 3: Handle missing values or non-numeric placeholder characters
# Convert columns to float, coercing invalid values (like '-' or '*') to NaN
for col in df_pivot.columns:
    df_pivot[col] = pd.to_numeric(df_pivot[col], errors='coerce')

# Step 4: Create Gender_Obesity_Gap column (Female Obesity - Male Obesity)
df_pivot['Gender_Obesity_Gap'] = df_pivot['Obesity_Women'] - df_pivot['Obesity_Men']

# Add average/combined columns for analysis
df_pivot['Obesity_Adult_Avg'] = (df_pivot['Obesity_Women'] + df_pivot['Obesity_Men']) / 2
df_pivot['Blood_Sugar_Avg'] = (df_pivot['Blood_Sugar_Women'] + df_pivot['Blood_Sugar_Men']) / 2
df_pivot['Hypertension_Avg'] = (df_pivot['Hypertension_Women'] + df_pivot['Hypertension_Men']) / 2

# Rename state names in the pivoted CSV to match the GeoJSON ST_NM exactly
state_rename_map = {
    'Andaman & Nicobar Islands': 'Andaman & Nicobar',
    'Dadra & Nagar Haveli and Daman & Diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'NCT Delhi': 'Delhi'
}
df_pivot.index = df_pivot.index.map(lambda s: state_rename_map.get(s, s))

# Drop national-level summary ('India') so we only retain state-level data
df_pivot = df_pivot.drop(index='India', errors='ignore')

# Output data summary
print("\nCleaned and Structured State-Level DataFrame:")
print(f"Cleaned DataFrame Shape: {df_pivot.shape}")
print(df_pivot.head(5))

print("\n--- PHASE 2: Exploratory Data Analysis (EDA) and Plotting ---")

# Task 1: Correlation Matrix calculation
# Calculate the Pearson correlation coefficient between Anaemia in children and Obesity in adults
corr_women = df_pivot['Anaemia_Children'].corr(df_pivot['Obesity_Women'], method='pearson')
corr_men = df_pivot['Anaemia_Children'].corr(df_pivot['Obesity_Men'], method='pearson')
corr_avg = df_pivot['Anaemia_Children'].corr(df_pivot['Obesity_Adult_Avg'], method='pearson')

print("\nPearson Correlation Coefficients (Children Anaemia vs. Adult Obesity):")
print(f"  - Correlation with Women Obesity: {corr_women:.4f}")
print(f"  - Correlation with Men Obesity:   {corr_men:.4f}")
print(f"  - Correlation with Average Adult Obesity: {corr_avg:.4f}")

# Task 2: Bar Chart - top 10 states with highest rates of hypertension in men vs women
top_10_ht = df_pivot.sort_values(by='Hypertension_Avg', ascending=False).head(10)

plt.figure(figsize=(12, 7))
# Set background style for premium feel
plt.gca().set_facecolor('#f8fafc')
plt.grid(True, linestyle='--', alpha=0.5, zorder=0)

# X positions for grouped bar chart
import numpy as np
x = np.arange(len(top_10_ht))
width = 0.35

# Plot grouped bars
plt.bar(x - width/2, top_10_ht['Hypertension_Women'], width, label='Women (Hypertension)', color='#f43f5e', zorder=3)
plt.bar(x + width/2, top_10_ht['Hypertension_Men'], width, label='Men (Hypertension)', color='#0ea5e9', zorder=3)

plt.title('Top 10 Indian States with the Highest Rates of Hypertension (Men vs Women)', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('State Name', fontsize=12, fontweight='bold', labelpad=10)
plt.ylabel('Prevalence Rate (%)', fontsize=12, fontweight='bold', labelpad=10)
plt.xticks(x, top_10_ht.index, rotation=30, ha='right', fontsize=10)
plt.legend(frameon=True, facecolor='white', edgecolor='none', fontsize=11)
plt.tight_layout()

# Save Hypertension Bar Chart
bar_chart_filename = 'hypertension_bar.png'
plt.savefig(bar_chart_filename, dpi=300)
plt.close()
print(f"Saved grouped bar chart as {bar_chart_filename}")

# Task 3: Scatter Plot - Percentage of Anaemic Women (X) vs. Percentage of Obese Women (Y)
state_abbrs = {
    'Andaman & Nicobar': 'AN', 'Andhra Pradesh': 'AP', 'Arunachal Pradesh': 'AR',
    'Assam': 'AS', 'Bihar': 'BR', 'Chandigarh': 'CH', 'Chhattisgarh': 'CG',
    'Dadra and Nagar Haveli and Daman and Diu': 'DN', 'Delhi': 'DL', 'Goa': 'GA',
    'Gujarat': 'GJ', 'Haryana': 'HR', 'Himachal Pradesh': 'HP', 'Jammu & Kashmir': 'JK',
    'Jharkhand': 'JH', 'Karnataka': 'KA', 'Kerala': 'KL', 'Ladakh': 'LA',
    'Lakshadweep': 'LD', 'Madhya Pradesh': 'MP', 'Maharashtra': 'MH', 'Manipur': 'MN',
    'Meghalaya': 'ML', 'Mizoram': 'MZ', 'Nagaland': 'NL', 'Odisha': 'OD',
    'Puducherry': 'PY', 'Punjab': 'PB', 'Rajasthan': 'RJ', 'Sikkim': 'SK',
    'Tamil Nadu': 'TN', 'Telangana': 'TG', 'Tripura': 'TR', 'Uttar Pradesh': 'UP',
    'Uttarakhand': 'UK', 'West Bengal': 'WB'
}

regions = {
    'Andaman & Nicobar': 'South & Islands', 'Andhra Pradesh': 'South',
    'Arunachal Pradesh': 'Northeast', 'Assam': 'Northeast', 'Bihar': 'East',
    'Chandigarh': 'North & UT', 'Chhattisgarh': 'Central',
    'Dadra and Nagar Haveli and Daman and Diu': 'West & UT', 'Delhi': 'North & UT',
    'Goa': 'West', 'Gujarat': 'West', 'Haryana': 'North', 'Himachal Pradesh': 'North',
    'Jammu & Kashmir': 'North', 'Jharkhand': 'East', 'Karnataka': 'South',
    'Kerala': 'South', 'Ladakh': 'North & UT', 'Lakshadweep': 'South & Islands',
    'Madhya Pradesh': 'Central', 'Maharashtra': 'West', 'Manipur': 'Northeast',
    'Meghalaya': 'Northeast', 'Mizoram': 'Northeast', 'Nagaland': 'Northeast',
    'Odisha': 'East', 'Puducherry': 'South & Islands', 'Punjab': 'North',
    'Rajasthan': 'North', 'Sikkim': 'Northeast', 'Tamil Nadu': 'South',
    'Telangana': 'South', 'Tripura': 'Northeast', 'Uttar Pradesh': 'Central',
    'Uttarakhand': 'North', 'West Bengal': 'East'
}

# Attach Region and Abbreviation
df_pivot['Abbr'] = df_pivot.index.map(state_abbrs)
df_pivot['Region'] = df_pivot.index.map(regions)

# Plotting scatter plot with region color mapping
plt.figure(figsize=(12, 8))
plt.gca().set_facecolor('#f8fafc')
plt.grid(True, linestyle='--', alpha=0.5, zorder=0)

unique_regions = sorted(list(set(regions.values())))
colors = ['#e11d48', '#2563eb', '#16a34a', '#d97706', '#7c3aed', '#0891b2', '#4b5563']
region_colors = {r: colors[i % len(colors)] for i, r in enumerate(unique_regions)}

# Plot each region separately to get correct legend
for r in unique_regions:
    sub_df = df_pivot[df_pivot['Region'] == r]
    plt.scatter(sub_df['Anaemia_Women'], sub_df['Obesity_Women'], 
                s=100, alpha=0.85, 
                color=region_colors[r], label=r, 
                edgecolors='#0f172a', linewidths=0.8, zorder=3)

# Label the points with abbreviations
for state, row in df_pivot.iterrows():
    abbr = row['Abbr'] if pd.notnull(row['Abbr']) else state[:3].upper()
    plt.annotate(abbr, (row['Anaemia_Women'], row['Obesity_Women']),
                 xytext=(5, 5), textcoords='offset points',
                 fontsize=9, fontweight='bold', alpha=0.8, zorder=4)

plt.title('Prevalence of Anaemic Women vs. Obese Women by Indian State (NFHS-5)', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Percentage of Anaemic Women (%)', fontsize=12, fontweight='bold', labelpad=10)
plt.ylabel('Percentage of Obese Women (%)', fontsize=12, fontweight='bold', labelpad=10)
plt.legend(title='Regions', frameon=True, facecolor='white', edgecolor='none', fontsize=10, title_fontsize=11)
plt.tight_layout()

# Save Scatter Plot
scatter_filename = 'correlation_scatter.png'
plt.savefig(scatter_filename, dpi=300)
plt.close()
print(f"Saved scatter plot as {scatter_filename}")

print("\n--- PHASE 3: Geographic Visualization (Folium) ---")

# Step 1: Initialize a Folium map of India centered at [20.5937, 78.9629]
india_map = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="cartodbpositron")

# Step 2: Bind GeoJSON file of India's state boundaries to DataFrame
with open(GEOJSON_PATH, 'r') as file:
    geojson_data = json.load(file)

# Build Choropleth layer
# Map the color scale to represent the prevalence of Average Adult Obesity
choropleth = Choropleth(
    geo_data=geojson_data,
    name="Adult Obesity Prevalence (%)",
    data=df_pivot,
    columns=[df_pivot.index, 'Obesity_Adult_Avg'],
    key_on="feature.properties.ST_NM",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Average Adult Obesity Prevalence (%)",
    highlight=True
).add_to(india_map)

# Add hover tooltips to choropleth boundary layers
# This allows hovering anywhere on a state boundary to see the state name and obesity rate.
folium.features.GeoJsonTooltip(
    fields=["ST_NM"],
    aliases=["State: "],
    labels=True,
    sticky=True,
    style="font-family: sans-serif; font-size: 13px; background-color: #ffffff; border: 1px solid #cccccc; border-radius: 4px; padding: 4px;"
).add_to(choropleth.geojson)

# Step 3: Add custom interactive CircleMarker layers over each state capital
capital_coordinates = {
    'Andaman & Nicobar': [11.6234, 92.7265],
    'Andhra Pradesh': [16.5062, 80.6480],
    'Arunachal Pradesh': [27.0844, 93.6053],
    'Assam': [26.1433, 91.7898],
    'Bihar': [25.5941, 85.1376],
    'Chandigarh': [30.7333, 76.7794],
    'Chhattisgarh': [21.2514, 81.6296],
    'Dadra and Nagar Haveli and Daman and Diu': [20.3974, 72.8328],
    'Delhi': [28.6139, 77.2090],
    'Goa': [15.4909, 73.8278],
    'Gujarat': [23.2156, 72.6369],
    'Haryana': [30.7398, 76.7827],
    'Himachal Pradesh': [31.1048, 77.1734],
    'Jammu & Kashmir': [34.0837, 74.7973],
    'Jharkhand': [23.3441, 85.3096],
    'Karnataka': [12.9716, 77.5946],
    'Kerala': [8.5241, 76.9366],
    'Ladakh': [34.1526, 77.5771],
    'Lakshadweep': [10.5667, 72.6417],
    'Madhya Pradesh': [23.2599, 77.4126],
    'Maharashtra': [19.0760, 72.8777],
    'Manipur': [24.8170, 93.9368],
    'Meghalaya': [25.5788, 91.8831],
    'Mizoram': [23.7271, 92.7176],
    'Nagaland': [25.6751, 94.1086],
    'Odisha': [20.2961, 85.8245],
    'Puducherry': [11.9416, 79.8083],
    'Punjab': [30.7046, 76.7179],
    'Rajasthan': [26.9124, 75.7873],
    'Sikkim': [27.3314, 88.6138],
    'Tamil Nadu': [13.0827, 80.2707],
    'Telangana': [17.3850, 78.4867],
    'Tripura': [23.8315, 91.2868],
    'Uttar Pradesh': [26.8467, 80.9462],
    'Uttarakhand': [30.3165, 78.0322],
    'West Bengal': [22.5726, 88.3639]
}

for state_name, coords in capital_coordinates.items():
    if state_name in df_pivot.index:
        row = df_pivot.loc[state_name]
        
        # Build premium tooltip html layout
        tooltip_html = f"""
        <div style="
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 12px;
            background-color: #1e293b;
            color: #f8fafc;
            border-radius: 8px;
            border: 1px solid #475569;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
            min-width: 230px;
        ">
            <h4 style="margin: 0 0 6px 0; color: #f59e0b; border-bottom: 2px solid #475569; padding-bottom: 4px; font-size: 15px;">{state_name}</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <tr>
                    <td style="padding: 3px 0; color: #94a3b8;">Avg Obesity:</td>
                    <td style="padding: 3px 0; text-align: right; font-weight: bold; color: #fbbf24;">{row['Obesity_Adult_Avg']:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 3px 0; color: #94a3b8; padding-left: 8px;">Women / Men:</td>
                    <td style="padding: 3px 0; text-align: right; color: #cbd5e1;">{row['Obesity_Women']:.1f}% / {row['Obesity_Men']:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 3px 0; color: #94a3b8; font-weight: bold;">High Blood Sugar:</td>
                    <td style="padding: 3px 0; text-align: right; font-weight: bold; color: #f87171;">{row['Blood_Sugar_Avg']:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 3px 0; color: #94a3b8; padding-left: 8px;">Women / Men:</td>
                    <td style="padding: 3px 0; text-align: right; color: #cbd5e1;">{row['Blood_Sugar_Women']:.1f}% / {row['Blood_Sugar_Men']:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 3px 0; color: #94a3b8; font-weight: bold;">Anaemia:</td>
                    <td style="padding: 3px 0; text-align: right; font-weight: bold; color: #60a5fa;">{row['Anaemia_Women']:.1f}% (W)</td>
                </tr>
                <tr>
                    <td style="padding: 3px 0; color: #94a3b8; padding-left: 8px;">Children / Men:</td>
                    <td style="padding: 3px 0; text-align: right; color: #cbd5e1;">{row['Anaemia_Children']:.1f}% / {row['Hypertension_Men']:.1f}%</td>
                </tr>
            </table>
        </div>
        """
        
        # Add CircleMarker representing the capital city
        CircleMarker(
            location=coords,
            radius=6,
            color='#1e293b',
            fill=True,
            fill_color='#f59e0b',
            fill_opacity=0.9,
            weight=1.5,
            tooltip=tooltip_html,
            popup=Popup(tooltip_html, max_width=300)
        ).add_to(india_map)

# Save Interactive Map Dashboard
dashboard_filename = "india_health_dashboard.html"
india_map.save(dashboard_filename)
print(f"Saved interactive Folium dashboard as {dashboard_filename}")
print("\nExecution completed successfully!")

# =============================================================================
# The purpose of this script is to generate a division-level demographic
# context file for LAPD divisions using areal interpolation. Census tract
# race and population data from the ACS (2017–2022) is spatially allocated
# to LAPD divisions by weighting raw population counts by the fraction of
# each census tract's area that falls within a given division. Percentages
# are derived from the interpolated counts rather than averaged across tracts,
# keeping the math consistent with the division as the unit of analysis.
# Output is a panel dataset indexed by Division_ID and Year.

# Notes: Intersection pairs with area weights below 0.001 were excluded 
# (n = 241 unique tract-division pairs, distributed across all 21 divisions), 
# as these represent boundary artifacts where a census tract nominally overlaps 
# a neighboring division by less than 0.1% of its area, contributing negligible 
# population estimates.
# =============================================================================

import geopandas as gpd
import pandas as pd
import glob
import os
import numpy as np

# ===== Load shapefiles =======================================================

census_tracts = gpd.read_file('data/2020_Census_Tracts')
lapd_divisions = gpd.read_file("data/LAPD_Division_-8371726096393184647.geojson")

# ===== Standardize to same CRS ===============================================

census_tracts = census_tracts.to_crs(epsg=32611)
lapd_divisions = lapd_divisions.to_crs(epsg=32611)

# Compute census tract area from geometry before intersection so units are
# guaranteed consistent with Intersecting_Area_SqF computed below
census_tracts['Census_Tract_Area_SqF'] = (census_tracts.geometry.area * 10.7639).astype(int)

# ===== Intersect geometries ==================================================

intersected = gpd.overlay(census_tracts, lapd_divisions, how='intersection')

intersected['Intersecting_Area_SqF'] = (intersected.geometry.area * 10.7639).astype(int)

# Rename
rename_dict = {
    'CT20': 'Census_Tract_ID',
    'Census_Tract_Area_SqF': 'Census_Tract_Area_SqF',
    'PREC': 'Division_ID',
    'APREC': 'Division_Name'
}
intersected = intersected.rename(columns=rename_dict)

# Keep only what is needed downstream
intersected = intersected[[
    'Census_Tract_ID', 'Census_Tract_Area_SqF',
    'Division_ID', 'Division_Name',
    'Intersecting_Area_SqF', 'geometry'
]]

# Export crosswalk
no_geo = intersected.drop(columns='geometry')


# ===== Load and clean race data ==============================================

race_folder = 'data/ACSDT5Y2017-2022.B03002'
race = pd.DataFrame()

# Column names changed between ACS releases; backup covers 2017 and 2018
race_rename_dict = {
    'Geography': 'Census_Tract_ID',
    'Estimate!!Total:': 'Total_Population',
    'Estimate!!Total:!!Not Hispanic or Latino:!!White alone': 'Population_White',
    'Estimate!!Total:!!Not Hispanic or Latino:!!Black or African American alone': 'Population_Black_African_American',
    'Estimate!!Total:!!Not Hispanic or Latino:!!American Indian and Alaska Native alone': 'Population_American_Indian_Alaska_Native',
    'Estimate!!Total:!!Not Hispanic or Latino:!!Asian alone': 'Population_Asian',
    'Estimate!!Total:!!Not Hispanic or Latino:!!Native Hawaiian and Other Pacific Islander alone': 'Population_Native_Hawaiian_Other_Pacific_Islander',
    'Estimate!!Total:!!Not Hispanic or Latino:!!Some other race alone': 'Population_Some_Other_Race',
    'Estimate!!Total:!!Not Hispanic or Latino:!!Two or more races:': 'Population_Two_Or_More_Races',
    'Estimate!!Total:!!Hispanic or Latino:': 'Total_Population_Hispanic_Latino'
}

race_rename_dict_backup = {
    'Geography': 'Census_Tract_ID',
    'Estimate!!Total': 'Total_Population',
    'Estimate!!Total!!Not Hispanic or Latino!!White alone': 'Population_White',
    'Estimate!!Total!!Not Hispanic or Latino!!Black or African American alone': 'Population_Black_African_American',
    'Estimate!!Total!!Not Hispanic or Latino!!American Indian and Alaska Native alone': 'Population_American_Indian_Alaska_Native',
    'Estimate!!Total!!Not Hispanic or Latino!!Asian alone': 'Population_Asian',
    'Estimate!!Total!!Not Hispanic or Latino!!Native Hawaiian and Other Pacific Islander alone': 'Population_Native_Hawaiian_Other_Pacific_Islander',
    'Estimate!!Total!!Not Hispanic or Latino!!Some other race alone': 'Population_Some_Other_Race',
    'Estimate!!Total!!Not Hispanic or Latino!!Two or more races': 'Population_Two_Or_More_Races',
    'Estimate!!Total!!Hispanic or Latino': 'Total_Population_Hispanic_Latino'
}

population_columns = [
    'Total_Population',
    'Population_White',
    'Population_Black_African_American',
    'Population_American_Indian_Alaska_Native',
    'Population_Asian',
    'Population_Native_Hawaiian_Other_Pacific_Islander',
    'Population_Some_Other_Race',
    'Population_Two_Or_More_Races',
    'Total_Population_Hispanic_Latino'
]

race_columns_to_keep = list(race_rename_dict.values())

for file_path in glob.glob(os.path.join(race_folder, '*.csv')):
    try:
        file_name = os.path.basename(file_path)
        year = file_name[-20:-16]

        data = pd.read_csv(file_path, skiprows=1)

        if set(race_rename_dict.keys()).issubset(data.columns):
            rename_dict_to_use = race_rename_dict
        elif set(race_rename_dict_backup.keys()).issubset(data.columns):
            rename_dict_to_use = race_rename_dict_backup
        else:
            print(f"No suitable column renaming dictionary found for {file_path}. Skipping...")
            continue

        data = data.rename(columns=rename_dict_to_use)
        data = data[race_columns_to_keep]
        data['Census_Tract_ID'] = data['Census_Tract_ID'].str[-6:]
        data[population_columns] = data[population_columns].apply(pd.to_numeric, errors='coerce')
        data['Year'] = year

        race = pd.concat([race, data], ignore_index=True)

    except Exception as e:
        print(f"An error occurred with file {file_path}: {e}")


# ===== Merge crosswalk with race data ========================================

merged_data = pd.merge(no_geo, race, on='Census_Tract_ID', how='left')
merged_data.dropna(subset=population_columns, inplace=True)
merged_data[population_columns] = merged_data[population_columns].astype(int)


# ===== Areal interpolation ===================================================

# Fraction of each census tract that falls inside each division sliver
merged_data['Area_Weight'] = merged_data['Intersecting_Area_SqF'] / merged_data['Census_Tract_Area_SqF']

# Remove boundary artifacts: census tract-division pairs where the intersecting
# area is less than 0.1% of the census tract's total area. Diagnostic analysis
# confirmed these represent geometric boundary noise distributed evenly across
# all 21 divisions (241 unique pairs), not data loss in any specific area.
AREA_WEIGHT_THRESHOLD = 0.001
merged_data = merged_data[merged_data['Area_Weight'] > AREA_WEIGHT_THRESHOLD]

# Scale raw counts by area weight to estimate population within each sliver
for col in population_columns:
    merged_data[f'{col}_Estimated'] = merged_data[col] * merged_data['Area_Weight']

estimated_columns = [f'{col}_Estimated' for col in population_columns]

# Sum estimated counts up to the division level — stay in count space until all
# slivers are aggregated, then compute proportions from the division totals
grouped = merged_data.groupby(['Division_ID', 'Division_Name', 'Year'])[estimated_columns].sum().reset_index()


# ===== Compute race percentages from interpolated division totals =============

# Map each race group label to its estimated count column
race_groups = [
    'White',
    'Black_African_American',
    'American_Indian_Alaska_Native',
    'Asian',
    'Native_Hawaiian_Other_Pacific_Islander',
    'Some_Other_Race',
    'Two_Or_More_Races',
    'Hispanic_Latino'
]

race_count_col_map = {
    'White':                                  'Population_White_Estimated',
    'Black_African_American':                 'Population_Black_African_American_Estimated',
    'American_Indian_Alaska_Native':          'Population_American_Indian_Alaska_Native_Estimated',
    'Asian':                                  'Population_Asian_Estimated',
    'Native_Hawaiian_Other_Pacific_Islander': 'Population_Native_Hawaiian_Other_Pacific_Islander_Estimated',
    'Some_Other_Race':                        'Population_Some_Other_Race_Estimated',
    'Two_Or_More_Races':                      'Population_Two_Or_More_Races_Estimated',
    'Hispanic_Latino':                        'Total_Population_Hispanic_Latino_Estimated'
}

for group, count_col in race_count_col_map.items():
    grouped[f'Percent_{group}'] = (grouped[count_col] / grouped['Total_Population_Estimated'] * 100).round(2)


# ===== Assemble final output =================================================

# Column order: identifiers → total population → raw group counts → proportions
id_cols    = ['Division_ID', 'Division_Name', 'Year']
count_cols = ['Total_Population_Estimated'] + [race_count_col_map[g] for g in race_groups]
percent_cols = [f'Percent_{g}' for g in race_groups]

comm_context = grouped[id_cols + count_cols + percent_cols].copy()

# Rename count columns: drop _Estimated suffix, add Division_ prefix
count_rename = {
    'Total_Population_Estimated':                                      'Division_Total_Population',
    'Population_White_Estimated':                                      'Division_Population_White',
    'Population_Black_African_American_Estimated':                     'Division_Population_Black_African_American',
    'Population_American_Indian_Alaska_Native_Estimated':              'Division_Population_American_Indian_Alaska_Native',
    'Population_Asian_Estimated':                                      'Division_Population_Asian',
    'Population_Native_Hawaiian_Other_Pacific_Islander_Estimated':     'Division_Population_Native_Hawaiian_Other_Pacific_Islander',
    'Population_Some_Other_Race_Estimated':                            'Division_Population_Some_Other_Race',
    'Population_Two_Or_More_Races_Estimated':                          'Division_Population_Two_Or_More_Races',
    'Total_Population_Hispanic_Latino_Estimated':                      'Division_Population_Hispanic_Latino'
}
comm_context = comm_context.rename(columns=count_rename)
comm_context = comm_context.round(2)


# ===== Export ================================================================

comm_context.to_csv('output/division_race_variables.csv', index=False)
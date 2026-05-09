# Spatial Data Merge
This repository contains community context data (2017-2022) for the Everday Respect project, and the code needed to merge these data at the reporting district level. Where applicable, artifacts representing the analyses outputs are included. A data dictionary is available for future analysis and use on Airtable (ask team member for access) and statically here: [`LAPD Data Dictionary.xlsx`](LAPD_Data_Dictionary.xlsx)


## Getting started
This repository is organized into two folders: [`data`](./data/), [`output`](./output/). The [`data`](./data/) folder contains sub-folders. 

Unzip all files in the directory [`data`](./data/) and any subfolders. These files are too large to be pushed into GitHub unzipped, but the code will not run without them. 

## Running analysis

To run the code, Jupyter Notebook and Python are required. All code is contained within the Jupyter Notebook file [`spatial_merge.ipynb`](spatial_merge.ipynb) organized with headings and sub-headings. To run this file, install all package requirements (under `Imports`) using [pip](https://pypi.org/project/pip/) or your preferred package installer. You may need to restart the kernel to access the packages. 

No other modifications are required to run the script. 

The output figures and data files will be added to the [`output`](./output/) directory. 

### Methods and use
We used an area-weighted average approach to aggregate demographic and income variables from the census tract to the reporting district level. The initial variables came from two ACS datasets reported at the census tract level:
- American Community Survey (ACS) Table B03002 (5-year estimates for race and ethnicity)
- American Community Survey (ACS) Table S1901 (5-year estimates of household income)

Vintages for 2017, 2018, 2019, 2020, 2021, and 2022 were used for both ACS datasets. See [data dictionary](LAPD_Data_Dictionary.xlsx) for more details.

We performed a spatial overlay using the [Geopandas library](https://geopandas.org/en/stable/docs.html) to identify and calculate the intersecting areas between census tracts and reporting districts. A look-up table of the census tracts to reporting districts is available for future merges: [`CT_to_RD_lookup.csv`](./output/CT_to_RD_lookup.csv). A visual depiction of the intersection is also produced: [`CT_to_RD_merge.png`](./output/CT_to_RD_merge.png).

We calculated weighted averages for each year for each variable based on the area of each census tract within the reporting district. The (area-weighted averaged) variables for each reporting district include:
- Median Household Income (Dollars)
- Percentage of White Population
- Percentage of Black/African American Population
- Percentage of American Indian/Alaska Native Population
- Percentage of Asian Population
- Percentage of Native Hawaiian/Other Pacific Islander Population
- Percentage of Some Other Race Population
- Percentage of Two or More Races Population
- Percentage of Hispanic/Latino Population

These variables are output into the file [`community_context_variables.csv`](./output/community_context_variables.csv). 

Arrest and calls for service data were already available at the reporting district level and did not need to undergo the spatial overlay process. These data were captured into a separate file – [`lapd_demand_variables.csv`](./output/lapd_demand_variables.csv). 

This was for two reasons: 
1. It's a lengthy file!
2. To capture the data at the finest temporal resolution (dates) since merging with the community context variables would require rolling up to the year level.

The data can be matched on `Reporting_District_ID` since that column name is consistent across both files. 

## 05/09/2026 Update: Division-level demographic context

A parallel pipeline was developed to aggregate race and population data from the census tract to the LAPD division level, contained in [`racial_spatial_merge.py`](racial_spatial_merge.py). LAPD divisions are a higher-level administrative geography, where 21 divisions cover the city, each composed of multiple reporting districts.

The only new data source introduced is the LAPD Divisions shapefile ([LA City GeoHub](https://geohub.lacity.org/datasets/lapd-divisions)), stored at `data/LAPD_Division_-8371726096393184647.geojson`. All ACS race data (Table B03002, vintages 2017–2022) is drawn from the same `data/ACSDT5Y2017-2022.B03002/` folder used in the original pipeline.

Rather than area-weighted averages, this pipeline uses areal interpolation. For each census tract-division intersection, raw population counts are scaled by the fraction of the census tract's area that falls within the division. These estimated counts are summed to the division level before percentages are computed, ensuring race shares are derived from division-level population totals rather than averaged across tracts.

Intersection pairs with area weights below 0.001 were excluded prior to interpolation (241 unique tract-division pairs distributed evenly across all 21 divisions), as these represent geometric boundary noise rather than meaningful overlap.

The output file [`division_race_variables.csv`](./output/division_race_variables.csv) is a panel dataset indexed by `Division_ID` and `Year` containing estimated population counts and race shares for each division. The data can be matched to other division-level files on `Division_ID`.
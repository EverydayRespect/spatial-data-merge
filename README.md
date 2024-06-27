# Spatial Data Merge
This repository contains community context data (2017-2022) for the Everday Respect project, and the code needed to merge these data at the reporting district level. Where applicable, artifacts representing the analyses outputs are included.


## Getting started
This repository is organized into two folders: [`data`](./data/), [`output`](./output/). The [`data`](./data/) folder contains sub-folders. 

Unzip all files in the directory [`data`](./data/) and any subfolders. These files are too large to be pushed into GitHub unzipped, but the code will not run without them. 

## Running analysis

To run the code, Jupyter Notebook and Python are required. All code is contained within the Jupyter Notebook file [`spatial_merge.ipynb`](spatial_merge.ipynb) organized with headings and sub-headings. To run this file, install all package requirements (under `Imports`) using pip or your preferred package installer. You may need to restart the kernel to access the packages. 

No other modifications are required to run the script. 

The output figures and data files will be added to the [`output`](./output/) directory. 

### Methods and use
We used an area-weighted average approach to aggregate demographic and income variables from the census tract to the reporting district level. The initial variables came from two ACS datasets reported at the census tract level:
- American Community Survey (ACS) Table B03002 (5-year estimates for race and ethnicity)
- American Community Survey (ACS) Table S1901 (5-year estimates of household income)

Vintages for 2017, 2018, 2019, 2020, 2021, and 2022 were used for both ACS datasets.

We performed a spatial overlay using the [Geopandas library](https://geopandas.org/en/stable/docs.html) to identify and calculate the intersecting areas between census tracts and reporting districts.

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

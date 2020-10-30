"""
    AWS_Download.py version: 0.6 (29 October 2020) by: David J. Cartwright davidcartwright@hotmail.com
        Created and tested on ArcPro 2.6.2

    This script downloads specified LANDSAT Rasters from AWS. Script is meant to be run by an ArcPro Toolbox
    Inputs:
        URL: of AWS scene list, example: https://landsat-pds.s3.amazonaws.com/c1/L8/scene_list.gz

    Outputs:
        Band 1-11 of scenes selected, saved to disk optionally added to current map.
"""

import arcpy
import datetime
import numpy as np
import pandas as pd
import time
import urllib.request

P_OUTPUT_INDEX = 6

scene_list = arcpy.GetParameter(0)
start_date = arcpy.GetParameter(1)
end_date = arcpy.GetParameter(2)
scene_path = arcpy.GetParameter(3)
scene_row = arcpy.GetParameter(4)
max_results = arcpy.GetParameter(5)
output_folder = arcpy.GetParameter(P_OUTPUT_INDEX)
add_to_map = arcpy.GetParameter(7)
create_composite = arcpy.GetParameter(8)

band_list = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}

arcpy.AddMessage("Downloading Scene List from AWS")
try:
    scenelist = pd.read_csv(scene_list)
except Exception as e:
    arcpy.AddError("Could not access AWS Scene List (CSV)")
    exit(-1)
nrows, ncols = scenelist.shape
arcpy.AddMessage(f"Download complete: {nrows} scenes listed.")

# Filter by Path
arcpy.AddMessage("Filtering by Path")
filter_list = scenelist[scenelist['path'] == scene_path]
nrows, ncols = filter_list.shape
arcpy.AddMessage(f"Filtering by Path resulted in {nrows} scenes.")

arcpy.AddMessage("Filtering by Row")
filter_list = filter_list[filter_list['row'] == scene_row]
nrows, ncols = filter_list.shape
arcpy.AddMessage(f"Filtering by Row resulted in {nrows} scenes.")

# Format 'acquisitionDate' as Date, Sort descending
arcpy.AddMessage(f"Sorting by 'acquisitionDate'.")
filter_list['acquisitionDate'] = pd.to_datetime(filter_list['acquisitionDate'])
filter_list.sort_values(by=['acquisitionDate'],inplace=True, ascending=False)


arcpy.AddMessage("Filtering by Dates")
count = 0

match_indexes = list()
#   Need to add an AND less tha or equal to
for index, row in filter_list.iterrows():
    #if (parser.parse(row['acquisitionDate']).date() >= start_date.date() and parser.parse(row['acquisitionDate']).date() <= end_date.date()):
    if (row['acquisitionDate']>= start_date.date() and row['acquisitionDate'] <= end_date.date()):
        arcpy.AddMessage(f"Found match: {row['productId']}")
        match_indexes.append(index)
        count += 1
        if count == max_results:
            arcpy.AddMessage(f"Filtering reached Maximum.")
            break

if count == 0:
    arcpy.AddWarning(f"Filtering resulted in no scenes matching the query.")

else:
    arcpy.AddMessage(f"Filtering resulted in {count} rows.")

# Determine urls for all scene indexes and download
for i in match_indexes:
    # arcpy.AddMessage(i)
    raster_url = filter_list.loc[i, 'download_url']
    raster_list = ""
    for b in band_list:
        dl_url = raster_url[0:len(raster_url)-10]+raster_url.split("/")[8]+"_B"+str(b)+".TIF"
        base_fname = raster_url.split("/")[8]
        dl_filename = raster_url.split("/")[8]+"_B"+str(b)+".TIF"
        arcpy.AddMessage(f"Downloading band:{b}: '{dl_filename}'")
        urllib.request.urlretrieve(dl_url, output_folder.value + "\\" + dl_filename)
        raster_list += output_folder.value + "\\" + dl_filename + ";"
        # Add the downloaded Raster to Current Map

        if add_to_map:
            try:
                aprx = arcpy.mp.ArcGISProject('CURRENT')
                rasTempLyr = arcpy.MakeRasterLayer_management(output_folder.value + "\\" + dl_filename, "test")
                activeMap = aprx.activeMap
                activeMap.addDataFromPath(output_folder.value + "\\" + dl_filename)

            except:
                arcpy.AddError("Could not add Raster to current map.")

        dl_url = ""
        composite_name = base_fname
        base_fname = ""

    # Build Composite of All Bands
    if create_composite:
        arcpy.AddMessage(f"Creating Composite of all bands: {composite_name}")
        raster_list = raster_list[:-1]
        arcpy.CompositeBands_management(raster_list, composite_name)
        composite_name = ""






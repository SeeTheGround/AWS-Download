"""
    AWS_Download.py version: 0.6 (29 October 2020) by: David J. Cartwright davidcartwright@hotmail.com
        Created and tested on ArcPro 2.6.2

    https://github.com/SeeTheGround/AWS-Download

    This script downloads specified LANDSAT Rasters from AWS. Script is meant to be run by an ArcPro Toolbox
    Inputs:
        URL: of AWS scene list, example: https://landsat-pds.s3.amazonaws.com/c1/L8/scene_list.gz

    Outputs:
        Band 1-11 of scenes selected, saved to disk optionally added to current map.

    Requirements:
        Toolbox with the following parameters: https://github.com/SeeTheGround/AWS-Download/blob/main/Tool%20Properties.png
            [note] default scene list - https://landsat-pds.s3.amazonaws.com/c1/L8/scene_list.gz"""

P_SCENE_LIST = 0        # AWS Scene List [String] - path the AWS scene list
P_START_DATE = 1        # Start Date [Date] - Start date for scene search
P_END_DATE = 2          # End Date [Date] - End date for search
P_SCENE_PATH = 3        # Path [Long] path number of landsat scene for search
P_SCENE_ROW = 4         # Row [Long] row number of landsat scene for search
P_MAX_SCENES = 5        # Max Results [Long] Maximum number of unique scenes to download
P_OUTPUT_FOLDER = 6     # Location where downloaded scenes will be saved
P_ADD_TO_MAP = 7        # [Boolean] If TRUE, downloaded scene/bands will be added to current MAP
P_CREATE_COMP = 8       # [Boolean] If TRUE, all downloaded scenes will have bands combines in a file

import arcpy
import datetime
import numpy as np
import pandas as pd
import time
import urllib.request



scene_list = arcpy.GetParameter(P_SCENE_LIST)
start_date = arcpy.GetParameter(P_START_DATE)
end_date = arcpy.GetParameter(P_END_DATE)
scene_path = arcpy.GetParameter(P_SCENE_PATH)
scene_row = arcpy.GetParameter(P_SCENE_ROW)
max_results = arcpy.GetParameter(P_MAX_SCENES)
output_folder = arcpy.GetParameter(P_OUTPUT_FOLDER)
add_to_map = arcpy.GetParameter(P_ADD_TO_MAP)
create_composite = arcpy.GetParameter(P_CREATE_COMP)

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






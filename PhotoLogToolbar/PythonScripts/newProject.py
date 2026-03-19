# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING. If not, write to the
# Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

######################################
##  ------------------------------- ##
##           newProject.py          ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  17-Oct-2017   ##
##  ------------------------------- ##
######################################

# Import Built-In Libraries
import os
import math
import sys
import shutil
import time
from datetime import datetime
import subprocess
import importlib
# Import Arcpy
try:
    arcpy
except:
    print('Importing arcpy...')
    print('')
    import arcpy

# Import Custom Libraries that DO NOT require arcpy
import ExifParser
importlib.reload(ExifParser)
import osConvenience
importlib.reload(osConvenience)
import JLog
importlib.reload(JLog)
import backup_images
importlib.reload(backup_images)
import fovUpdater
importlib.reload(fovUpdater)

# Create PrintLog Class
L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Delete=True)

# Enable Overwritting Geoprocessing Outputsw
arcpy.env.overwriteOutput = True

# define install folder path
#install_folder = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
install_folder = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# FUNCTION DEFINITIONS

def add_all_fields(feature_class_path):
    """
    Adds all required fields with the correct data types to the PhotoPoints feature class.
    This replaces the need for a template feature class.
    """
    L.Wrap("Adding required fields to PhotoPoints feature class...")
    # Field Name, Field Type, Field Alias, Field Length
    fields_to_add = [
        ("Number", "SHORT", "Photo Number"),
        ("Date", "DATE", "Date"),
        ("Time", "TEXT", "Time", 30), 
        ("Heading", "TEXT", "Heading", 50),
        ("Comment", "TEXT", "Comment", 500),
        ("Orientation", "TEXT", "Orientation", 50),
        ("ViewHeight", "DOUBLE", "View Height"),
        ("MetersOfView", "DOUBLE", "Meters of View"),
        ("Photographer", "TEXT", "Photographer", 100),
        ("USACE_ID", "TEXT", "USACE ID", 50),
        ("Project_Name", "TEXT", "Project Name", 255),
        ("Camera", "TEXT", "Camera", 100),
        ("LongEdgeFOV", "DOUBLE", "Long Edge FOV"),
        ("ShortEdgeFOV", "DOUBLE", "Short Edge FOV"),
        ("AspectRatio", "DOUBLE", "Aspect Ratio"),
        ("PhotoPath", "TEXT", "Photo Path", 500),
        ("POINT_X", "DOUBLE", "Longitude"),
        ("POINT_Y", "DOUBLE", "Latitude"),
        ("LocationSource", "TEXT", "Location Source", 150),
        ("HeadingSource", "TEXT", "Heading Source", 150),
        ("Asterisk", "TEXT", "Asterisk", 150),
        ("Asterisk2", "TEXT", "Asterisk 2", 150),
        ("timezone", "TEXT", "Time Zone", 50),
        ("OverviewScale", "DOUBLE", "OverviewScale")
    ]
    
    for field_info in fields_to_add:
        field_name = field_info[0]
        field_type = field_info[1]
        field_alias = field_info[2]
        field_length = field_info[3] if len(field_info) > 3 else None
        
        L.Wrap(f"- Adding field: {field_name} ({field_type})")
        arcpy.management.AddField(
            in_table=feature_class_path,
            field_name=field_name,
            field_type=field_type,
            field_alias=field_alias,
            field_length=field_length
        )


def Offset(Lat,Lon,Degrees,Meters=1000):
    # Earth's Radius in meters, sphere
    R = 6378137
    # Offset in Meters
    mLat = math.cos(math.radians(Degrees))*Meters
    mLon = math.sin(math.radians(Degrees))*Meters
    # Coordinate offset in radians
    dLat = mLat/R
    dLon = mLon/(R*math.cos(math.pi*Lat/180))
    # Offset position, decimal degrees
    Lat0 = Lat + dLat * 180/math.pi
    Lon0 = float(Lon) + float(dLon * 180/math.pi)
    del R, mLat, mLon, dLat, dLon
    return Lat0,Lon0

def createPhotoPoints(GDB, PhotoFolder, ProjectName, USACE_ID, Photographer, RawPhotoPoints=None):
    Start = time.perf_counter()
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=6)
    PhotoPoints = f"{GDB}\\PhotoPoints" 
    fovPath = f"{GDB}\\FOV"
    # 4326 is the EPSG code for WGS 1984
    sr_wgs_1984 = arcpy.SpatialReference(4326) 
    L.Wrap('RawPhotoPoints = ')
    if str(RawPhotoPoints) == 'None':
        RawPhotoPoints = None
    L.Wrap('---Start of createPhotoPoints()---')
    # Get list of images in PhotoFolder
    L.Wrap('Getting list of all images in PhotoFolder...')
    images = list(filter(lambda x: x.lower().endswith(('.jpg', '.jpeg', '.png', '.tif')), os.listdir(PhotoFolder)))
    photo_paths = []
    exclude_list = ['(R090)', '(R180)', '(R270)']
    for name in images:
        excluded = False
        for exclude_string in exclude_list:
            if exclude_string in name:
                excluded = True
        if excluded is False:
            photo_paths.append(PhotoFolder + '\\' + name)
    # Create exiftool Instance
    L.Wrap('Creating instance of ExifParser...')
    temp_ET = ExifParser.Wrapper()
    # Calculate Time Shift between DateTaken and GPS_DateTime
    ModeOfTimeDifferences = temp_ET.GetModeOfTimeDifferences(photo_paths)
    del temp_ET # Immediately discared the temporary instance
    L.Wrap('')
    L.Wrap('')
    L.Wrap('')
    # Now, create a new, clean instance for the main processing loop.
    L.Wrap('Creating main instance of ExifParser for processing...')
    ET = ExifParser.Wrapper()
    # Manually set the mode we just calculated.
    ET.ModeOfTimeDifference = ModeOfTimeDifferences
    # Creating Insert Cursor
    L.Wrap('Creating arcpy.da.InsertCursor()...')
    check = arcpy.Exists(PhotoPoints)
    fields = ['SHAPE@X', 'SHAPE@Y', 'Number', 'Date', 'Time', 'Heading', 'Comment', 'Orientation', 'ViewHeight',
              'MetersOfView', 'Photographer', 'USACE_ID', 'Project_Name', 'Camera', 'LongEdgeFOV',
              'ShortEdgeFOV', 'AspectRatio', 'PhotoPath', 'POINT_X', 'POINT_Y', 'LocationSource', 'HeadingSource',
              'timezone', 'OverviewScale']
    
    # Define Workspace & Create editor
    edit = arcpy.da.Editor(GDB)
    # Start an edit session (multiuser_mode = False for File GDB)
    edit.startEditing(False, False)
    edit.startOperation()

    # Create Insert cursors
    with arcpy.da.InsertCursor(PhotoPoints, fields) as IC_PhotoPoints, \
        arcpy.da.InsertCursor(fovPath, ['SHAPE@', 'Number']) as IC_FOV:
        # Using InsertCursor to add a row for each photo
        Num = 0
        L.Wrap('Using Insert Cursor to add a row for each photo...')
        for photo_path in photo_paths:
            # Acquire Metadata from Photo using ExifParser.Wrapper instance
            ET.GetMetadata(photo_path)
            # Get row values
            row = []
            X_Coord = ET.X_Coord()
            Y_Coord = ET.Y_Coord()
            Num += 1
            Date = ET.Date()
            Time = ET.Time()
            Heading = ET.Heading()
            Description = ''
            Orientation = ET.Orientation()
            ViewHeight = 1000
            MetersOfView = 1000
            Camera = ET.Camera()
            LongEdgeFOV = ET.LongEdgeFOV()
            ShortEdgeFOV = ET.ShortEdgeFOV()
            AspectRatio = ET.AspectRatio()
            row.append(X_Coord)
            row.append(Y_Coord)
            row.append(Num)
            row.append(Date)
            row.append(Time)
            row.append(Heading)
            row.append(Description)
            row.append(Orientation)
            row.append(1000)
            row.append(1000)
            row.append(Photographer)
            row.append(USACE_ID)
            row.append(ProjectName)
            row.append(Camera)
            row.append(LongEdgeFOV)
            row.append(ShortEdgeFOV)
            row.append(AspectRatio)
            row.append(photo_path)
            row.append(X_Coord)
            row.append(Y_Coord)
            if X_Coord == 0:
                row.append('')
            else:
                row.append("Camera's internal GPS")
            if Heading == "":
                row.append('N//A')
            else:
                row.append("Camera's internal compass")
            row.append(ET.GetTimeZone()[1])
            row.append(6000) # Overview Scale
            tup = tuple(row)
            IC_PhotoPoints.insertRow(tup)
            # Create FOV Polygon
            if Heading == "":
                Polygon = None
            else:
                # Determine Angle of View
                if Orientation == 'Landscape':
                    AOV = LongEdgeFOV
                if Orientation == 'Portrait':
                    AOV = ShortEdgeFOV
                # Duplicating a variable because not using Lat/Lon in the formula below makes my head woozy
                Lon = X_Coord
                Lat = Y_Coord
                # Calculate azmuth for each offset point
                p1_Degrees = Heading + AOV/2
                p2_Degrees = Heading - AOV/2
                # Calculate Hypotenuse Distance
                HypDist = MetersOfView/(math.cos(math.radians(AOV/2)))
                # Calculate offset coordinates
                p1_Coords = Offset(Lat, Lon, p1_Degrees, HypDist)
                p2_Coords = Offset(Lat, Lon, p2_Degrees, HypDist)
                # Create Point objects
                p0 = arcpy.Point(Lon, Lat)
                p1 = arcpy.Point(p1_Coords[1], p1_Coords[0])
                p2 = arcpy.Point(p2_Coords[1], p2_Coords[0])
                # Create point array
                Array = arcpy.Array([p0, p1, p2, p0])
                # Create Polygon geometry object
                Polygon = arcpy.Polygon(Array, sr_wgs_1984)
                del AOV,Lon,Lat,p1_Degrees,p2_Degrees,HypDist,p1_Coords,p2_Coords,p0,p1,p2,Array
            # Use insert cursor and polygon to create new row if update failed
            IC_FOV.insertRow([Polygon, Num])
            # Garbage collection
            del X_Coord,Y_Coord,Date,Time,Heading,Description,Orientation,ViewHeight,MetersOfView,
            del Camera,LongEdgeFOV,ShortEdgeFOV,AspectRatio,Polygon
            
    # Close the edit session for the workspace
    edit.stopOperation()
    edit.stopEditing(True) # True saves changes
    # Calculate AspectRation
    AspectRatio = ET.AspectRatio()
#    taken_date = str(ET.Date())[:10]
    # Terminate ExifParser class
    L.Wrap('Terminating PyExifToolWrapper class...')
#    ET.Terminate()
    del ET
    # Create Update Cursor using SQL Clause to re-order by actual taken date
    check = arcpy.Exists(PhotoPoints)
    NewRow = 1
    fields = ['Number', 'Date', 'Time']
    with arcpy.da.UpdateCursor(PhotoPoints, fields, sql_clause=(None, 'ORDER BY Date, Time')) as cursor:
        # Re-number rows based on Date and Time sorting
        for row in cursor:
            row[0] = NewRow
            NewRow += 1
            cursor.updateRow(row)
    # Sync PhotoPoints with TerraSync Photographs Shapefile, if provided
    if RawPhotoPoints is not None:
        # Create Search Cursor and parse all fields
        L.Wrap('Creating SearchCursor...')
        fields = ['SHAPE@X', 'SHAPE@Y', 'Number', 'Date', 'Time', 'Heading', 'Comment', 'Rcvr_Type']
        X = []
        Y = []
        Number = []
        Date = []
        Time = []
        Heading = []
        Comment = []
        Rcvr_Type = []
        check = arcpy.Exists(RawPhotoPoints)
        with arcpy.da.SearchCursor(RawPhotoPoints, fields, sql_clause=(None, 'ORDER BY Number')) as SC:
            for row in SC:
                X.append(row[0])
                Y.append(row[1])
                Number.append(row[2])
                Date.append(row[3])
                Time.append(row[4])
                Heading.append(row[5])
                Comment.append(row[6])
                if row[7] == 'Pro 6T':
                    Rcvr_Type.append('Trimble Pro 6T')
                else:
                    Rcvr_Type.append(row[7])
        # Create Update Cursor using SQL Clause to Re-order by number
        L.Wrap('Creating UpdateCursor...')
        check = arcpy.Exists(PhotoPoints)
        fields = ['SHAPE@X', 'SHAPE@Y', 'Number', 'Date', 'Time', 'Heading', 'Comment',
                  'POINT_X', 'POINT_Y', 'LocationSource', 'HeadingSource']
        with arcpy.da.UpdateCursor(PhotoPoints, fields, sql_clause=(None, 'ORDER BY Number')) as cursor:
            # Update fields with values from Trimble Photographs Shapefile
            Num = 0
            for row in cursor:
                L.Wrap(Num)
                row[0] = X[Num]
                row[1] = Y[Num]
                if ModeOfTimeDifferences == None:
                    row[3] = Date[Num]
                if ModeOfTimeDifferences == None:
                    row[4] = Time[Num]
                row[5] = Heading[Num]
                row[6] = '' + str(Comment[Num])
                row[7] = X[Num]
                row[8] = Y[Num]
                row[9] = Rcvr_Type[Num]
                row[10] = 'Compass'
                Num += 1
                cursor.updateRow(row)
        # Update the FOV Polygons to reflect any changes to the Photo Location layer
        L.Wrap('Updating FOV Polygons to reflect changes from Trimble Points')
        fovUpdater.Simple(photo_location_path=PhotoPoints, fov_path=fovPath)
    L.Time(Start,'updatePhotoPoints()')
    del Start
    L.Wrap('----End of createPhotoPoints()----')
    del L, images, Num, check
    return AspectRatio




def Main(PhotoFolder,
         OutputFolder,
         ProjectName,
         USACE_ID,
         Photographer,
         RawPhotoPoints=None):
    Start = time.perf_counter()
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=3)
    try:
        L.Wrap('Backing up all photographs to an encrypted ".7z" file with the password "ChainOfCustody"...')
        backup_images.compress_photos(PhotoFolder)
    except Exception:
        L.Wrap('Backup operation failed!')
    L.Wrap(' ')
    L.Wrap(' ')
    L.Wrap('---Start of NewProjectFromPoints()---')
    # Local Variables
    # Reference the project currently open in ArcGIS Pro for name checking
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    
    # Get a taken_date for naming checks before the main processing
    images = filter(lambda x: x.lower().endswith(('.jpg', '.jpeg', '.png', '.tif')), os.listdir(PhotoFolder))
    photo_paths = []
    # Remove images that a the result of previous 'Rotate 90 Degrees' operations
    exclude_list = ['(R090)', '(R180)', '(R270)']
    for name in images:
        excluded = False
        for exclude_string in exclude_list:
            if exclude_string in name:
                excluded = True
        if excluded is False:
            photo_paths.append(PhotoFolder + '\\' + name)
    # Get first image
    first_image_path = photo_paths[0]
    taken_date = "YYYY-MM-DD" # Default date
    if first_image_path:
        try:
            ET_check = ExifParser.Wrapper()
            ET_check.GetMetadata(first_image_path)
            taken_date = str(ET_check.Date())[:10]
        except Exception as e:
            L.Wrap(f"Could not pre-fetch date for naming, using default. Error: {e}")
    L.Wrap(f"Photograph 'Taken Date' = {taken_date}")
    

    # 1. New centralized logic to find a unique suffix for all assets
    L.Wrap('Finding a unique name suffix for folder, layout, and maps...')
    augment = 1
    name_suffix = ""
    while True:
        # Proposed names
        prospective_folder = f'{OutputFolder}\\Mapped Photo Log{name_suffix}'
        prospective_layout_name = f"{taken_date} - Mapped Photo Log{name_suffix}"
        prospective_main_map_name = f"{taken_date} - Photo Log - Main{name_suffix}"
        prospective_overview_map_name = f"{taken_date} - Photo Log - Overview{name_suffix}"

        # Check if any of the prospective names already exist
        folder_exists = os.path.exists(prospective_folder)
        layout_exists = aprx.listLayouts(prospective_layout_name)
        main_map_exists = aprx.listMaps(prospective_main_map_name)
        overview_map_exists = aprx.listMaps(prospective_overview_map_name)

        if not folder_exists and not layout_exists and not main_map_exists and not overview_map_exists:
            L.Wrap(f"Suffix '{name_suffix}' is available. Locking it in.")
            break  # Found a unique suffix, exit the loop

        # If names are taken, increment and try again
        L.Wrap(f"Suffix '{name_suffix}' is in use. Trying next number.")
        name_suffix = f" {augment}" # Adds a space as requested
        augment += 1

    # 2. Define final names using the determined unique suffix
    ProjectFolder = f'{OutputFolder}\\Mapped Photo Log{name_suffix}'
    GDB = ProjectFolder + '\\GIS_Data.gdb'
    PhotoPoints = GDB + '\\PhotoPoints'
    fovPath = GDB + '\\FOV'
    mpPath = GDB + '\\MarkerPoint'

    template_folder = install_folder + r'\Template Files'
    PhotoPointTemplate = install_folder + r'\Template Files\Photo Location.lyr'
    FOVTemplate = install_folder + r'\Template Files\Field of View.lyr'
    MarkerPointTemplate = install_folder + r'\Template Files\Marker Point.lyr'
    OverviewPhotoPointTemplate = install_folder + r'\Template Files\Photo Location (Overview).lyr'
    # Create Project Folder
    L.Wrap('Creating Main Project Folder...')
    osConvenience.ensure_dir(ProjectFolder)
    # Create File Geodatabase
    L.Wrap('Checking for GDB...')
    if os.path.exists(GDB) == False:
        L.Wrap('Creating File Geodatabase...')
        try:
            arcpy.CreateFileGDB_management(ProjectFolder,'GIS_Data')
            xx = arcpy.GetMessages()
            L.Wrap(xx)
        except:
            L.Wrap('Geodatabase creation failed...')
            xx = arcpy.GetMessages()
            L.Wrap(xx)
            time.sleep(30)

    # Create PhotoPoints Feature Class using reference
    L.Wrap('Creating PhotoPoints Feature Class using reference file...')
    template_path = install_folder + r'\Template Files\GIS_Data.gdb\PhotoPoints'
    spatial_reference_path = install_folder + r'\Template Files\WGS_1984.prj'
    with arcpy.EnvManager(XYResolution="0.0000000000001 Unknown"):
        arcpy.management.CreateFeatureclass(
            out_path=GDB,
            out_name="PhotoPoints",
            geometry_type="POINT",
            template=template_path,
            has_m="DISABLED",
            has_z="DISABLED",
            spatial_reference='GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],VERTCS["EGM96_Geoid",VDATUM["EGM96_Geoid"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Foot_US",0.3048006096012192]];-400 -400 11258999068426.2;-100000 3048.00609601219;-100000 10000;8.98315284119521E-09;3.28083333333333E-03;0.001;IsHighPrecision',
            config_keyword="",
            spatial_grid_1=0,
            spatial_grid_2=0,
            spatial_grid_3=0,
            out_alias="",
            oid_type="SAME_AS_TEMPLATE"
        )
#        # Add all required fields
#        add_all_fields(PhotoPoints)

        # Create FOV Polygon Feature Class
        fovFC = arcpy.management.CreateFeatureclass(
            out_path=GDB,
            out_name="FOV",
            geometry_type="POLYGON",
            template=None,
            has_m="DISABLED",
            has_z="DISABLED",
            spatial_reference='GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],VERTCS["EGM96_Geoid",VDATUM["EGM96_Geoid"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Foot_US",0.3048006096012192]];-400 -400 11258999068426.2;-100000 3048.00609601219;-100000 10000;8.98315284119521E-09;3.28083333333333E-03;0.001;IsHighPrecision',
            config_keyword="",
            spatial_grid_1=0,
            spatial_grid_2=0,
            spatial_grid_3=0,
            out_alias="",
            oid_type="SAME_AS_TEMPLATE"
        )

        # Create Marker Point Feature Class
        mpFC = arcpy.management.CreateFeatureclass(
            out_path=GDB,
            out_name="MarkerPoint",
            geometry_type="POINT",
            template=None,
            has_m="DISABLED",
            has_z="DISABLED",
            spatial_reference='GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],VERTCS["EGM96_Geoid",VDATUM["EGM96_Geoid"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Foot_US",0.3048006096012192]];-400 -400 11258999068426.2;-100000 3048.00609601219;-100000 10000;8.98315284119521E-09;3.28083333333333E-03;0.001;IsHighPrecision',
            config_keyword="",
            spatial_grid_1=0,
            spatial_grid_2=0,
            spatial_grid_3=0,
            out_alias="",
            oid_type="SAME_AS_TEMPLATE"
        )

    # Add Number field to fovFC
    arcpy.management.AddField(fovFC, "Number", "SHORT")
    
    # Copying TerraSync Photographs Feature Class using reference
    TerraSync_Photographs = None
    if str(RawPhotoPoints) != "None":    
        L.Wrap('Creating TerraSync Photographs Feature Class...')
        arcpy.FeatureClassToFeatureClass_conversion(in_features=RawPhotoPoints,
                                                    out_path=GDB,
                                                    out_name='TerraSync_Photographs')
        TerraSync_Photographs = GDB + '\\TerraSync_Photographs'
    
    # UPDATE ALL PhotoPoints FIELDS (Also provides the Aspect Ratio for choosing the Layout Template)
    L.Wrap('executing updatePhotoPoints()...')
    AspectRatio = createPhotoPoints(GDB,
                                    PhotoFolder,
                                    ProjectName,
                                    USACE_ID,
                                    Photographer,
                                    TerraSync_Photographs)
    L.Wrap('AspectRatio = ' + str(AspectRatio))
    
    # Select the 4x3 Layout File by default to catch alternate aspect ratios
    template_pagx = template_folder + r'\Mapped Photo Log (4x3).pagx' 
    if AspectRatio > .70 and AspectRatio < .80:
        L.Wrap('Choosing the 4x3 Photo Layout MXD...')  
        template_pagx = template_folder + r'\Mapped Photo Log (4x3).pagx'
    if AspectRatio > .60 and AspectRatio < .70:
        L.Wrap('Choosing the 3x2 Photo Layout MXD...')
        template_pagx = template_folder + r'\Mapped Photo Log (3x2).pagx'
    
    # Use a "before and after" comparison to reliably find the imported layout.
    # Get the list of all layout names BEFORE importing.
    layouts_before = {lyt.name for lyt in aprx.listLayouts()}
    # Import the new layout from the template.
    aprx.importDocument(template_pagx)
    # Get the list of all layout names AFTER importing.
    layouts_after = {lyt.name for lyt in aprx.listLayouts()}
    # The new layout's name is the one in the 'after' set but not the 'before' set.
    new_layout_name = (layouts_after - layouts_before).pop()
    # Get the actual layout object by its unique name.
    new_lyt = aprx.listLayouts(new_layout_name)[0]

    # Now that we have the correct layout, rename it.
    new_lyt.name = f"{taken_date} - Mapped Photo Log{name_suffix}"

    # Rename and Update Data Sources
    for mf in new_lyt.listElements("MAPFRAME_ELEMENT"):
        if "Photo Log - Main" in mf.map.name:
            # Rename Map to avoid confusing clutter
            mf.map.name = f"{taken_date} - Photo Log - Main{name_suffix}"
            # Get Current "old" GDB path
            for lyr in mf.map.listLayers():
                if "Photo Location" in lyr.name:
                    L.Wrap(f'Testing Old GDB Path using {lyr.name} layer...')
                    try:
                        old_gdb = arcpy.Describe(lyr.dataSource).path
                        L.Wrap(f'-Old Geodatabase = {old_gdb}')
                    except:
                        L.Wrap("There is a problem with your Template Layout's Layer Data Source...")
                        raise
                    break
            # Update GDB Source
            L.Wrap(f'Executing MapFrame.Map.updateConnectionProperties(Old Geodatabase, New Geodatabase)...')
            mf.map.updateConnectionProperties(old_gdb, GDB)
            # Ensure All Layers are enabled
            for lyr in mf.map.listLayers():
                if not lyr.visible:
                    lyr.visible = True
                    L.Wrap(f"- Layer '{lyr.name}' in map '{mf.map.name}' has been turned ON.")
        elif "Photo Log - Overview" in mf.map.name:
            mf.map.name = f"{taken_date} - Photo Log - Overview{name_suffix}"
            # Get Current "old" GDB path
            for lyr in mf.map.listLayers():
                if "Photo Location" in lyr.name:
                    L.Wrap(f'Testing Old GDB Path using {lyr.name} layer...')
                    try:
                        old_gdb = arcpy.Describe(lyr.dataSource).path
                        L.Wrap(f'-Old Geodatabase = {old_gdb}')
                    except:
                        L.Wrap("There is a problem with your Template Layout's Layer Data Source...")
                        raise
                    break
            # Update GDB Source
            L.Wrap(f'Executing MapFrame.Map.updateConnectionProperties(Old Geodatabase, New Geodatabase)...')
            mf.map.updateConnectionProperties(old_gdb, GDB)

    # Get the Map Series
    ms = new_lyt.mapSeries
    # Set Map Series to the First Page
    ms.currentPageNumber = 1

    # Open the layout and switch the view to it
    new_lyt.openView()

    # Final Refresh and Save
    aprx.save()

#    if EditBeforeRendering == True:
#        # Open MXD
#        L.Wrap('Opening mxd file in new ArcMap instance...')
#        subprocess.Popen(finalMXD,shell=True)
#    else:
#        # Export Sheets to PDF and then merge to final
#        L.Wrap('Running ExportWithMods() function...')
#        import exportWithMods
#        E = exportWithMods.ExportWithSub(MXD=finalMXD)
#        E()
    L.Time(Start,'NewProjectFromPoints()')
    del Start, ProjectFolder, GDB, PhotoPoints
    L.Wrap('----End of NewProjectFromPoints()----')
    del L

if __name__ == '__main__':
    Main(PhotoFolder=r'C:\Users\L2RCSJ9D\OneDrive - US Army Corps of Engineers\Documents\ArcGIS\Projects\PhotoLogToolbar\Test Projects\201500644 - Stewart Water Diversion\2016-06-14 - Site Visit\Photographs',
         OutputFolder=r'C:\Users\L2RCSJ9D\OneDrive - US Army Corps of Engineers\Documents\ArcGIS\Projects\PhotoLogToolbar\Test Projects\201500644 - Stewart Water Diversion\2016-06-14 - Site Visit',
         ProjectName='Stewart Water Diversion',
         USACE_ID='SPK-2015-00644',
         Photographer='Jason C. Deters',
         RawPhotoPoints=r'C:\Users\L2RCSJ9D\OneDrive - US Army Corps of Engineers\Documents\ArcGIS\Projects\PhotoLogToolbar\Test Projects\201500644 - Stewart Water Diversion\2016-06-14 - Site Visit\GPS Data\Photogr.shp')

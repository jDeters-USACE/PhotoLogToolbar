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

# Create PrintLog Class
L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Delete=True)

# Import Custom Libraries that DO require arcpy
import FieldUpdates

# Enable Overwritting Geoprocessing Outputsw
arcpy.env.overwriteOutput = True

# define install folder path
#install_folder = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
install_folder = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# FUNCTION DEFINITIONS

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
    print(type(Lon))
    print(type(dLon))
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
    images = filter(lambda x: x.lower().endswith(('.jpg', '.jpeg', '.png', '.tif')), os.listdir(PhotoFolder))
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
    ET = ExifParser.Wrapper()
    # Calculate Time Shift between DateTaken and GPS_DateTime
    ModeOfTimeDifferences = ET.GetModeOfTimeDifferences(photo_paths)
    # Hack to get list of attributes
    L.Wrap('')
    L.Wrap('')
    L.Wrap('')
    if Photographer == 'EXIF':
        for photo_path in photo_paths:
            ET.GetMetadata(photo_path)
            ET.X_Coord()
            ET.Y_Coord()
            ET.Date()
            ET.Time()
            ET.Heading()
            ET.Orientation()
            ET.Camera()
            ET.LongEdgeFOV()
            ET.ShortEdgeFOV()
            ET.AspectRatio()
            ET.GetTimeDifference()
            ET.GetTimeZone()
            L.Wrap('')
            L.Wrap('')
            ET.ListAllAttributes()
            L.Wrap('')
            L.Wrap('')
        ET.Terminate()
        return
    # Creating Insert Cursor
    L.Wrap('Creating arcpy.da.InsertCursor()...')
    check = arcpy.Exists(PhotoPoints)
    fields = ['SHAPE@X', 'SHAPE@Y', 'Number', 'Date', 'Time', 'Heading', 'Comment', 'Orientation', 'ViewHeight',
              'MetersOfView', 'Photographer', 'USACE_ID', 'Project_Name', 'Camera', 'LongEdgeFOV',
              'ShortEdgeFOV', 'AspectRatio', 'PhotoPath', 'POINT_X', 'POINT_Y', 'LocationSource', 'HeadingSource', 'timezone']
    
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
    Taken_Date = str(ET.Date())[:10]
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
    L.Time(Start,'updatePhotoPoints()')
    del Start
    L.Wrap('----End of createPhotoPoints()----')
    del L, images, Num, check
    return AspectRatio, Taken_Date







def Main(PhotoFolder,
         OutputFolder,
         ProjectName,
         USACE_ID,
         Photographer,
         RawPhotoPoints=None,
         EditBeforeRendering=False):
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
    TempFolder = r'C:\Temp\Mapped_PhotoLog'
    ProjectFolder = OutputFolder + '\\Mapped Photo Log'
    # Check if ProjectFolder already exists, and augment if it does
    augment = 1
    while os.path.exists(ProjectFolder):
        ProjectFolder = f'{OutputFolder}\\Mapped Photo Log{augment}'
        augment += 1
    # If there was no augmentation
    if augment < 2:
        # Make the augment nothing, so we can use this for the map names for the catalog.
        augment = ""
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
    # Debug -  announce vars
    L.Wrap(f'template path = {template_path}')
    arcpy.CreateFeatureclass_management(out_path=GDB,
                                        out_name="PhotoPoints",
                                        geometry_type="POINT",
                                        template=template_path,
                                        has_m='DISABLED',
                                        has_z='DISABLED',
                                        spatial_reference="GCS_WGS_1984")
    
    # Create FOV Polygon Feature Class
    fovFC = arcpy.CreateFeatureclass_management(out_path=GDB,
                                                out_name='FOV',
                                                geometry_type='POLYGON',
                                                template='#',
                                                has_m='DISABLED',
                                                has_z='DISABLED',
                                                spatial_reference="GCS_WGS_1984")
    arcpy.management.AddField(fovFC, "Number", "SHORT")

    # Create Marker Point Feature Class
    mpFC = arcpy.CreateFeatureclass_management(out_path=GDB,
                                               out_name='MarkerPoint',
                                               geometry_type='POINT',
                                               template='#',
                                               has_m='DISABLED',
                                               has_z='DISABLED',
                                               spatial_reference="GCS_WGS_1984")
    # Copying TerraSync Photographs Feature Class using reference
    TerraSync_Photographs = None
    if str(RawPhotoPoints) != "None":    
        L.Wrap('Creating TerraSync Photographs Feature Class...')
        arcpy.FeatureClassToFeatureClass_conversion(in_features=RawPhotoPoints,
                                                    out_path=GDB,
                                                    out_name='TerraSync_Photographs')
        TerraSync_Photographs = GDB + '\\TerraSync_Photographs'
    
    # UPDATE ALL PhotoPoints FIELDS (Also provides the Aspect Ratio for choosing the MXD)
    L.Wrap('executing updatePhotoPoints()...')
    AspectRatio, Taken_Date = createPhotoPoints(GDB,
                                                PhotoFolder,
                                                ProjectName,
                                                USACE_ID,
                                                Photographer,
                                                TerraSync_Photographs)
    L.Wrap('AspectRatio = ' + str(AspectRatio))
    L.Wrap(f'Date_Taken = {Taken_Date}')
    
    # Select the 4x3 Layout File by default to catch alternate aspect ratios
    template_pagx = template_folder + r'\Mapped Photo Log (4x3).pagx' 
    if AspectRatio > .70 and AspectRatio < .80:
        L.Wrap('Choosing the 4x3 Photo Layout MXD...')  
        template_pagx = template_folder + r'\Mapped Photo Log (4x3).pagx'
    if AspectRatio > .60 and AspectRatio < .70:
        L.Wrap('Choosing the 3x2 Photo Layout MXD...')
        template_pagx = template_folder + r'\Mapped Photo Log (3x2).pagx'
    
    # Reference the project currently open in ArcGIS Pro
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    # Import Layout File
    aprx.importDocument(template_pagx)

    # Rename the Layout (Reference the most recently added layout)
    new_lyt = aprx.listLayouts()[-1] 
    new_lyt.name = f"{Taken_Date} - Mapped Photo Log{augment}"

    # Rename and Update Data Sources
    for mf in new_lyt.listElements("MAPFRAME_ELEMENT"):
        if "Photo Log - Main" in mf.map.name:
            # Rename Map to avoid confusing clutter
            mf.map.name = f"{Taken_Date} - Photo Log - Main{augment}"
            # Get Current "old" GDB path
            lyr = mf.map.listLayers()[0]
            old_gdb = arcpy.Describe(lyr.dataSource).path
            # Update GDB Source
            mf.map.updateConnectionProperties(old_gdb, GDB)
        elif "Photo Log - Overview" in mf.map.name:
            mf.map.name = f"{Taken_Date} - Photo Log - Overview{augment}"
            # Get Current "old" GDB path
            lyr = mf.map.listLayers()[0]
            old_gdb = arcpy.Describe(lyr.dataSource).path
            # Update GDB Source
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
    del Start, TempFolder, ProjectFolder, GDB, PhotoPoints
    L.Wrap('----End of NewProjectFromPoints()----')
    del L

if __name__ == '__main__':
#    Main(PhotoFolder=r'R:\ORM\2009\200901482 - CAHST, Fresno to Bakersfield\Photos 200901482\Allensworth Impact Sites 3-27 to 3-28-17\Photos 3-27 to 3-28-17',
#         OutputFolder=r'R:\ORM\2009\200901482 - CAHST, Fresno to Bakersfield\Photos 200901482\Allensworth Impact Sites 3-27 to 3-28-17',
#         ProjectName='California High-Speed Rail, Fresno to Bakersfield Section',
#         USACE_ID='SPK-2009-01482',
#         Photographer='Zachary Simmons',
#         RawPhotoPoints=None,
#         EditBeforeRendering=False)
    
    Main(PhotoFolder=r'C:\Users\L2RCSJ9D\OneDrive - US Army Corps of Engineers\Documents\ArcGIS\Projects\PhotoLogToolbar\Test Projects\201500644 - Stewart Water Diversion\2016-06-14 - Site Visit\test\test\Photographs',
         OutputFolder=r'C:\Users\L2RCSJ9D\OneDrive - US Army Corps of Engineers\Documents\ArcGIS\Projects\PhotoLogToolbar\Test Projects\201500644 - Stewart Water Diversion\2016-06-14 - Site Visit\test\test',
         ProjectName='Wildlands Mitigation Bank',
         USACE_ID='SPK-1993-00362',
         Photographer='Denielle Wise',
         RawPhotoPoints=None,
         EditBeforeRendering=False)

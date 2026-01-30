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
##          featureOpsC.py          ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##    Last Edited on: 2018-06-05    ##
##  ------------------------------- ##
######################################

# Import Built-In Libraries
import os
import math
import sys
import shutil
import time
import datetime
import tkInputPrompt

# Import Custom Libraries that DO NOT require arcpy
import osConvenience
import JLog
import PyExifToolWrap

# Create PrintLog Class
L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Delete=True)

# Import Arcpy    
import arcpy
import pythonaddins

# Enable Overwritting Geoprocessing Outputs
arcpy.env.overwriteOutput = True

# define install folder path
install_folder = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]

# FUNCTION DEFINITIONS

def calculate_initial_compass_bearing(pointA, pointB):
    # jeromer, compassbearing.py, https://gist.github.com/jeromer/2005586#file-compassbearing-py
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")
    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])
    diffLong = math.radians(pointB[1] - pointA[1])
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))
    initial_bearing = math.atan2(x, y)
    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

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
    Lon0 = Lon + dLon * 180/math.pi
    del R, mLat, mLon, dLat, dLon
    return Lat0,Lon0

def pageXY_to_mapXY(page_x, page_y):
    mxd = arcpy.mapping.MapDocument("CURRENT")
    data_frame = arcpy.mapping.ListDataFrames(mxd,"Layers")[0]
    # get the data frame dimensions in page units  
    df_page_w = data_frame.elementWidth
    df_page_h = data_frame.elementHeight
    df_page_x_min = data_frame.elementPositionX
    df_page_y_min = data_frame.elementPositionY
    df_page_x_max = df_page_w + df_page_x_min
    df_page_y_max = df_page_h + df_page_y_min
    # get the data frame projected coordinates
    df_min_x = data_frame.extent.XMin
    df_min_y = data_frame.extent.YMin
    df_max_x = data_frame.extent.XMax
    df_max_y = data_frame.extent.YMax
    df_proj_w = data_frame.extent.width
    df_proj_h = data_frame.extent.height
    #ensure the coordinates are in the dataframe
    if page_x < df_page_x_min or page_x > df_page_x_max:
        raise ValueError('X coordinate is not within map portion of the page.')
    if page_y < df_page_y_min or page_y > df_page_y_max:
        raise ValueError('Y coordinate is not within map portion of the page.')
    #scale the projected coordinates to map units from the lower left of the data frame
    scale_x = (df_max_x - df_min_x)/(df_page_x_max - float(df_page_x_min))
    scale_y = (df_max_y - df_min_y)/(df_page_y_max - float(df_page_y_min))
    map_x = df_min_x + ((page_x - df_page_x_min)*scale_x)
    map_y = df_min_y + ((page_y - df_page_y_min)*scale_y)
##    pythonaddins.MessageBox("Coordiantes are (" + str(map_y) + ", " + str(map_x),"Title")
    return map_x, map_y


# CLASS DEFINITIONS

class Main(object):

    def __init__(self,MXD=None):
        # Create empty attributes
        self.Orientation = ""
        self.Heading = ""
        self.coordX = ""
        self.coordY = ""
        self.PhotoPath = ""
        self.LongEdgeFOV = ""
        self.ShortEdgeFOV = ""
        self.AspectRatio = ""
        self.MetersOfView = ""
        self.ViewHeight = ''
        self.Comment = ''
        self.AOV = ""
        self.MarkerShape = ""
        self.MarkerX = ""
        self.MarkerY = ""
        self.MarkerActive = False
        self.DirectionChanged = False
        self.LocationChanged = False
        self.HeadingSourceChangedByLocation = False
        self.OldHeading = ""
        self.OldMarkerShape = ""
        self.OldX = ""
        self.OldY = ""
        self.OldLocationSource = ''
        self.OldHeadingSource = ''
        self.OldAsterisk = ''
        self.OldAsterisk2 = ''
        self.EditorName = ''
        self.Date = ''
        self.L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=9)
        # Set addOutputsToMap to False
        arcpy.env.addOutputsToMap = False
        # Define Local Variables
        PhotoPointTemplate = install_folder + r'\Template Files\Photo Location.lyr'
        FOVTemplate = install_folder + r'\Template Files\Field of View.lyr'
        MarkerPointTemplate = install_folder + r'\Template Files\Marker Point.lyr'
        OverviewPhotoPointTemplate = install_folder + r'\Template Files\Photo Location (Overview).lyr'
        if MXD == None:
            MXD = 'CURRENT'
        if MXD == 'CURRENT' or str(MXD).endswith(".mxd"):
            self.mxd = arcpy.mapping.MapDocument(MXD)
        else:
            self.mxd = MXD
        self.LayersDF = arcpy.mapping.ListDataFrames(self.mxd,'Layers')[0]
        self.OverviewDF = arcpy.mapping.ListDataFrames(self.mxd,'Overview')[0]
        Layers = arcpy.mapping.ListLayers(self.mxd,'',self.LayersDF)
        for layer in Layers:
            if layer.name == 'PhotoPoints':
                # Get Layer Object
                self.PhotoPoints = layer
        # Turn off PhotoPoints Layer
        self.PhotoPoints.visible = False
        # Get GDB path from PhotoPoints layer
        ppPath = self.PhotoPoints.dataSource
#        GDB = os.path.split(ppPath)[0]
        GDB = 'in_memory'
        apPath = GDB + '\\Photo_Location'
        fovPath = GDB + '\\FOV'
        mpPath = GDB + '\\MarkerPoint'
        backupPath = GDB + '\\backupPhotoPoints'
        # Backup PhotoPoints data
        arcpy.FeatureClassToFeatureClass_conversion(ppPath, GDB, 'backupPhotoPoints')
        # Get Spatial References
        self.ppSR = arcpy.Describe(self.PhotoPoints).spatialReference
        self.layersSR = self.LayersDF.spatialReference
        # Remove any previous layers from dataframes
        self.ClearLocAndFOV()
        self.ClearMarker()
        # Create Feature Classes
        if arcpy.Exists(apPath) is False:
            apFC = arcpy.CreateFeatureclass_management(out_path=GDB,
                                                       out_name='Photo_Location',
                                                       geometry_type='POINT',
                                                       template='#',
                                                       has_m='DISABLED',
                                                       has_z='DISABLED',
                                                       spatial_reference=self.ppSR)
        if arcpy.Exists(fovPath) is False:
            fovFC = arcpy.CreateFeatureclass_management(out_path=GDB,
                                                        out_name='FOV',
                                                        geometry_type='POLYGON',
                                                        template='#',
                                                        has_m='DISABLED',
                                                        has_z='DISABLED',
                                                        spatial_reference=self.ppSR)
        if arcpy.Exists(mpPath) is False:
            mpFC = arcpy.CreateFeatureclass_management(out_path=GDB,
                                                       out_name='MarkerPoint',
                                                       geometry_type='POINT',
                                                       template='#',
                                                       has_m='DISABLED',
                                                       has_z='DISABLED',
                                                       spatial_reference=self.layersSR)
        # Create Layer Objects
        arcpy.RefreshCatalog(GDB)
        self.apLayer = arcpy.mapping.Layer(apPath)
        self.apLayer.name = 'Photo Location'
        self.fovLayer = arcpy.mapping.Layer(fovPath)
        self.fovLayer.name = 'Field of View'
        self.mpLayer = arcpy.mapping.Layer(mpPath)
        self.mpLayer.name = 'Marker Point'
        self.ov_apLayer = arcpy.mapping.Layer(apPath)
        self.ov_apLayer.name = 'Photo Location' 
        # Apply Symbology from Template Layers
        arcpy.ApplySymbologyFromLayer_management(in_layer=self.apLayer,
                                                 in_symbology_layer=PhotoPointTemplate)
        arcpy.ApplySymbologyFromLayer_management(in_layer=self.fovLayer,
                                                 in_symbology_layer=FOVTemplate)
        arcpy.ApplySymbologyFromLayer_management(in_layer=self.mpLayer,
                                                 in_symbology_layer=MarkerPointTemplate)
        arcpy.ApplySymbologyFromLayer_management(in_layer=self.ov_apLayer,
                                                 in_symbology_layer=OverviewPhotoPointTemplate)
        # Set addOutputsToMap to True
        arcpy.env.addOutputsToMap = True
        return

    def SelectCurrentImage(self):
        """Select current photo using currentPageID"""
        self.pageNum = self.mxd.dataDrivenPages.currentPageID
        Clause = 'Number = ' + str(self.pageNum)
        arcpy.SelectLayerByAttribute_management(in_layer_or_view=self.PhotoPoints,
                                                selection_type='NEW_SELECTION',
                                                where_clause=Clause)
        return

    def SearchCurrentImage(self):
        self.SelectCurrentImage()
        # Get attribute values for selected Image
        fields = ['Orientation', 'Heading', 'SHAPE@XY', 'PhotoPath', 'LongEdgeFOV', 'ShortEdgeFOV',
                  'AspectRatio', 'MetersOfView', 'SHAPE@', 'ViewHeight', 'Comment']
        with arcpy.da.SearchCursor(self.PhotoPoints, fields) as cursor:
            for row in cursor:
                self.Orientation = row[0]
                if row[1] == '' or row[1] == ' ':
                    self.Heading = ''
                else:
                    try:
                        self.Heading = float(row[1])
                    except:
                        self.Heading = ''
                self.coordX = row[2][0]
                self.coordY = row[2][1]
                self.PhotoPath = row[3]
                self.LongEdgeFOV = float(row[4])
                self.ShortEdgeFOV = float(row[5])
                self.AspectRatio = float(row[6])
                self.MetersOfView = row[7]
                self.Shape = row[8]
                self.ViewHeight = row[9]
                self.Comment = row[10]
        # Determine Angle of View
        if self.Orientation == 'Landscape':
            self.AOV = self.LongEdgeFOV
        if self.Orientation == 'Portrait':
            self.AOV = self.ShortEdgeFOV
        return

    def WriteActivePoint(self):
        updated = False
        with arcpy.da.UpdateCursor(self.apLayer, ['SHAPE@']) as cursor:
            for row in cursor:
                row[0] = self.Shape
                cursor.updateRow(row)
                updated = True
        if not updated:
            with arcpy.da.InsertCursor(self.apLayer, ['SHAPE@']) as cursor:
                cursor.insertRow([self.Shape])
        return

    def WriteFOVPolygon(self):
        # Test for Heading
        if type(self.Heading) != float:
            # Remove existing rows in FOV Feature Class
            with arcpy.da.UpdateCursor(self.fovLayer, ['SHAPE@']) as cursor:
                for row in cursor:
                    cursor.deleteRow()
            return
        Lon = self.coordX
        Lat = self.coordY
        # Calculate azmuth for each offset point
        p1_Degrees = self.Heading + self.AOV/2
        p2_Degrees = self.Heading - self.AOV/2
        # Calculate Hypotenuse Distance
        HypDist = self.MetersOfView/(math.cos(math.radians(self.AOV/2)))
        # Calculate offset coordinates
        p1_Coords = Offset(Lat, Lon, p1_Degrees, HypDist)
        p2_Coords = Offset(Lat, Lon, p2_Degrees, HypDist)
        # Create Point objects
        p0 = arcpy.Point(Lon, Lat)
        p1 = arcpy.Point(p1_Coords[1], p1_Coords[0])
        p2 = arcpy.Point(p2_Coords[1], p2_Coords[0])
        # Create point array
        Array = arcpy.Array([p0, p1, p2])
        # Create Polygon geometry object
        Polygon = arcpy.Polygon(Array, self.ppSR)
        # Update any existing rows in feature class
        updated = False
        with arcpy.da.UpdateCursor(self.fovLayer, ['SHAPE@']) as cursor:
            for row in cursor:
                row[0] = Polygon
                cursor.updateRow(row)
                updated = True
        if not updated:
            # Use insert cursor and polygon to create new row if update failed
            with arcpy.da.InsertCursor(self.fovLayer, ['SHAPE@']) as cursor:
                cursor.insertRow([Polygon])
        return

    def WriteMarkerPoint(self, x, y):
        # See if Marker Layer has been added to the map
        if self.MarkerActive is False:
            # Add Marker Point layer to the map
            arcpy.mapping.AddLayer(self.LayersDF, self.mpLayer)
            self.MarkerActive = True
        # Test whether x is a map or page coordinate (Map x would be western hemisphere, so negative)
        if x > 0:
            # Convert Page coordinates to Map Coordinates
            x, y = pageXY_to_mapXY(x, y)
        # Create point geometry using coordinates
        self.MarkerX = x
        self.MarkerY = y
        self.MarkerShape = arcpy.Point(x, y)
        # Update existing rows in Map Point Feature Class
        updated = False
        with arcpy.da.UpdateCursor(self.mpLayer, ['SHAPE@']) as cursor:
            for row in cursor:
                row[0] = self.MarkerShape
                cursor.updateRow(row)
                updated = True
        if not updated:
            # Creae a new row in the Map Point Feature Class with the Point if update fails
            with arcpy.da.InsertCursor(self.mpLayer, ['SHAPE@']) as cursor:
                cursor.insertRow([self.MarkerShape])
        # Refresh the active view
        arcpy.RefreshActiveView()
        return

    def GetEditorAndDate(self):
        self.EditorName = tkInputPrompt.RequestName()
        Today = datetime.date.today()
        m = str(Today.month)
        d = str(Today.day)
        y = str(Today.year)
        self.Date = m+'/'+d+'/'+y
        return

    def marker_to_location(self):
        self.SelectCurrentImage()
        # Test of marker exists
        if self.test_marker() is True:
            self.DirectionChanged = False
            self.LocationChanged = True
            if self.EditorName == '':
                self.GetEditorAndDate()
            with arcpy.da.UpdateCursor(self.PhotoPoints, ['SHAPE@', 'Number', 'POINT_X', 'POINT_Y',
                                                         'LocationSource', 'Asterisk',
                                                         'HeadingSource', 'Asterisk2']) as cursor:
                for row in cursor:
                    if int(self.pageNum) == int(row[1]):
                        self.OldNumber = row[1]
                        self.OldMarkerShape = row[0]
                        self.OldX = row[2]
                        self.OldY = row[3]
                        self.OldLocationSource = row[4]
                        self.OldAsterisk = row[5]
                        self.OldHeadingSource = row[6]
                        self.OldAsterisk2 = row[7]
                        row[0] = self.MarkerShape
                        row[2] = self.MarkerX
                        row[3] = self.MarkerY
                        if self.OldLocationSource == '' or ('imagery' in self.OldLocationSource) == True:
                            row[4] = 'Determined using satellite imagery*'
                            row[5] = '* Set by ' + self.EditorName + ' on ' + self.Date
                        else:
                            row[4] = row[4].strip('*') + '*'
                            row[5] = '* Corrected by ' + self.EditorName + ' on ' + self.Date
                        if row[7] != None:
                            self.HeadingSourceChangedByLocation = True
                            row[6] = row[6].strip('*') + '**'
                            row[7] = '**' + row[7].strip('*')
                        cursor.updateRow(row)
            # Re-calculate mapped geometry
            self.Refresh()
            return

    def bearing_to_marker(self):
        self.SelectCurrentImage()
        # Test if marker exists
        if self.test_marker() is True:
##            try:
##                # if available (10.3 or later), use ArcGIS built-in function to calculate heading
##                bearing = self.Shape.angleAndDistanceTo(self.MarkerShape)[0]
##            except:
##                # if lower than ArcGIS 10.3, use function to calculate bearing
            pointA = (self.coordY, self.coordX)
            pointB = (self.MarkerY, self.MarkerX)
            bearing = calculate_initial_compass_bearing(pointA, pointB)
            self.setHeading(bearing)
            return

    def setHeading(self, value):
        self.SelectCurrentImage()
        self.DirectionChanged = True
        self.LocationChanged = False
        if self.EditorName == '':
            self.GetEditorAndDate()
        # Write heading to PhotoPoints FC
        with arcpy.da.UpdateCursor(self.PhotoPoints, ['Number', 'Heading', 'HeadingSource', 'Asterisk', 'Asterisk2']) as cursor:
            for row in cursor:
                if int(self.pageNum) == int(row[0]):
                    self.OldNumber = row[0]
                    self.OldHeading = row[1]
                    self.OldHeadingSource = row[2]
                    self.OldAsterisk2 = row[4]
                    row[1] = value
                    if row[3] == None:
                        Asterisks = '*'
                    else:
                        Asterisks = '**'
                    if self.OldHeadingSource == '' or ('imagery' in self.OldHeadingSource) == True:
                        row[2] = 'Determined using satellite imagery' + Asterisks
                        row[4] = Asterisks + ' Set by ' + self.EditorName + ' on ' + self.Date
                    else:
                        row[2] = row[2].strip('*') + Asterisks
                        row[4] = Asterisks + ' Corrected by ' + self.EditorName + ' on ' + self.Date
                    cursor.updateRow(row)
        # Re-calculate mapped geometry
        self.Refresh()
        return

    def UndoChange(self):
        self.SelectCurrentImage()
        if self.DirectionChanged is True:
            # Write heading to PhotoPoints FC
            with arcpy.da.UpdateCursor(self.PhotoPoints, ['Heading', 'HeadingSource', 'Asterisk2']) as cursor:
                for row in cursor:
                    if int(self.pageNum) == int(self.OldNumber):
                        row[0] = self.OldHeading
                        row[1] = self.OldHeadingSource
                        row[2] = self.OldAsterisk2
                        cursor.updateRow(row)
            # Re-calculate mapped geometry
            self.Refresh()
            self.DirectionChanged = False
            return
        if self.LocationChanged is True:
            with arcpy.da.UpdateCursor(self.PhotoPoints, ['SHAPE@', 'POINT_X', 'POINT_Y',
                                                          'LocationSource', 'Asterisk',
                                                          'HeadingSource', 'Asterisk2']) as cursor:
                for row in cursor:
                    if int(self.pageNum) == int(self.OldNumber):
                        row[0] = self.OldMarkerShape
                        row[1] = self.OldX
                        row[2] = self.OldY
                        row[3] = self.OldLocationSource
                        row[4] = self.OldAsterisk
                        if self.HeadingSourceChangedByLocation == True:
                            row[5] = self.OldHeadingSource
                            row[6] = self.OldAsterisk2
                        cursor.updateRow(row)
            # Re-calculate mapped geometry
            self.Refresh()
            self.LocationChanged = False
            self.HeadingSourceChangedByLocation = False
            return

    def distance_to_marker(self):
        self.SelectCurrentImage()
        # Test if marker exists
        if self.test_marker() is True:
            try:
                # if available (10.3 or later) use ArcGIS built-in function to calculate distance
                distance = self.Shape.angleAndDistanceTo(self.MarkerShape)[1]
                self.setDistance(distance)
                return
            except:
                # Tell them about the need to upgrade to 10.3 or higher to use this feature
                pythonaddins.MessageBox('This function requires ArcGIS Desktop 10.3.1 or newer', 'ArcGIS Version Error', 0)
                return

    def setDistance(self, value):
        self.SelectCurrentImage()
##        Answer = pythonaddins.MessageBox('Apply this distance to every page of this Photo Log?', 'Apply to All?', 4)
##        if Answer == 'Yes':
##            FC = self.PhotoPoints.dataSource
##        if Answer == 'No':
##            FC = self.PhotoPoints
## # Disabled the above feature because it was annoying to have a popup every time you set the distance

        with arcpy.da.UpdateCursor(self.PhotoPoints, ['MetersOfView']) as cursor:
            for row in cursor:
                row[0] = value
                cursor.updateRow(row)
        self.Refresh()
        return

    def center_on_marker(self):
        # Test of marker exists
        if self.test_marker() is True:
            # Pan to Marker Point
            self.LayersDF.panToExtent(self.mpLayer.getSelectedExtent())
            arcpy.RefreshActiveView()
            return

    def test_marker(self):
        # Test of marker exists
        if self.MarkerActive is True:
            return True
        else:
            # Create notification window asking that the user create a marker before retrying
            Title = 'No Marker Point Exists'
            Message = ('Please select the Marker Point tool and click a point on the map '
                       'to create a Marker Point before running this tool again.')
            pythonaddins.MessageBox(Message, Title)
            return

    def Refresh(self):
        self.SelectCurrentImage()
        self.SearchCurrentImage()
        self.WriteActivePoint()
        self.WriteFOVPolygon()
        arcpy.RefreshActiveView()
        # Pan to Active Point
        self.LayersDF.panToExtent(self.PhotoPoints.getSelectedExtent())
        return

    def AddLayers(self):
        # Refresh layer content
        self.Refresh()
        # Add Layers to the Map
        arcpy.mapping.AddLayer(self.LayersDF, self.fovLayer, "TOP")
        arcpy.mapping.AddLayer(self.LayersDF, self.apLayer, "TOP")
        arcpy.mapping.AddLayer(self.OverviewDF, self.ov_apLayer, "TOP")
        # Pan to Active Point
        self.LayersDF.panToExtent(self.PhotoPoints.getSelectedExtent())
        return

    def ClearLocAndFOV(self):
        # Clear created elements from map
        for layer in arcpy.mapping.ListLayers(self.mxd, '', self.OverviewDF):
            if layer.name == 'Photo Location':
                arcpy.mapping.RemoveLayer(self.OverviewDF, layer)
        for layer in arcpy.mapping.ListLayers(self.mxd, '', self.LayersDF):
            if layer.name == 'Photo Location':
                arcpy.mapping.RemoveLayer(self.LayersDF, layer)
            if layer.name == 'Field of View':
                arcpy.mapping.RemoveLayer(self.LayersDF, layer)
        return

    def ClearMarker(self):
        Layers = arcpy.mapping.ListLayers(self.mxd, '', self.LayersDF)
        for layer in Layers:
            if layer.name == 'Marker Point':
                arcpy.mapping.RemoveLayer(self.LayersDF, layer)
        self.MarkerActive = False
        return

    def setOrientation(self, value):
        self.SelectCurrentImage()
        newPath = None
        if value == u"Rotate 90\xb0 CW":
            L.Wrap('Rotate 90 Degrees selected...')
            currentPath = self.PhotoPath
            currentPathNoExt, ext = os.path.splitext(currentPath)
            currentEnd = currentPathNoExt[-6:]
            L.Wrap('CurrentPath = ' + currentPath)
            endList = ['(R090)', '(R180)', '(R270)']
            if not currentEnd in endList:
                L.Wrap('First rotation')
                pathR090 = currentPathNoExt + '(R090)' + ext
                if not os.path.exists(pathR090):
                    arcpy.env.addOutputsToMap = False
                    arcpy.Rotate_management(currentPath, pathR090, "90")
                    arcpy.env.addOutputsToMap = True
                newPath = pathR090
            if currentEnd == '(R090)':
                L.Wrap('Second rotation')
                pathR180 = currentPathNoExt[:-6] + '(R180)' + ext
                if not os.path.exists(pathR180):
                    arcpy.env.addOutputsToMap = False
                    arcpy.Rotate_management(currentPath, pathR180, "90")
                    arcpy.env.addOutputsToMap = True
                newPath = pathR180
            elif currentEnd == '(R180)':
                L.Wrap('Third rotation')
                pathR270 = currentPathNoExt[:-6] + '(R270)' + ext
                if not os.path.exists(pathR270):
                    arcpy.env.addOutputsToMap = False
                    arcpy.Rotate_management(currentPath, pathR270, "90")
                    arcpy.env.addOutputsToMap = True
                newPath = pathR270
            elif currentEnd == '(R270)':
                L.Wrap('Fourth rotation')
                newPath = currentPathNoExt[:-6] + ext
            L.Wrap('newPath = ' + newPath)
##            # Get updated orientation using ExifTool
##            L.Wrap('Creating instance of PyExifToolWrap to get updated Orientation...')
##            ET = PyExifToolWrap.Wrapper()
##            ET.GetMetadata(newPath)
##            newOrientation = ET.Orientation()
##            L.Wrap('Terminating PyExifToolWrapper class...')
##            ET.Terminate()
##            del ET
            L.Wrap('Updating fields in PhotoPoints feature class...')
            with arcpy.da.UpdateCursor(self.PhotoPoints, ['Orientation', 'PhotoPath']) as cursor:
                for row in cursor:
                    if row[0] == 'Landscape':
                        newOrientation = 'Portrait'
                    else:
                        newOrientation = 'Landscape'
                    row[0] = newOrientation
                    row[1] = newPath
                    cursor.updateRow(row)
            L.Wrap('Field update complete.')
        else:
            with arcpy.da.UpdateCursor(self.PhotoPoints, ['Orientation']) as cursor:
                for row in cursor:
                    row[0] = value
                    cursor.updateRow(row)
        self.Refresh()
        return

    def setScale(self, value):
        self.SelectCurrentImage()
##        Answer = pythonaddins.MessageBox('Apply this scale to every page of this Photo Log?', 'Apply to All?', 4)
##        if Answer == 'Yes':
##            FC = self.PhotoPoints.dataSource # Apply changes to every feature
##        if Answer == 'No':
##            FC = self.PhotoPoints
## # Disabled the above feature because it was annoying to have a popup every time you set a scale
        with arcpy.da.UpdateCursor(self.PhotoPoints, ['ViewHeight']) as cursor:
            for row in cursor:
                row[0] = value
                cursor.updateRow(row)
        self.LayersDF.scale = value
        self.Refresh()
        return

    def setDescription(self, value):
        self.SelectCurrentImage()
        with arcpy.da.UpdateCursor(self.PhotoPoints, ['Comment']) as cursor:
            for row in cursor:
                row[0] = value
                cursor.updateRow(row)
        self.Refresh()
        return

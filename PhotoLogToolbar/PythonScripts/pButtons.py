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
##           pButtons.py            ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

# Import Built-In Libraries
import os
import math
import sys
import shutil
import time
from datetime import datetime
import arcpy
import pythonaddins

# Import Custom Libraries
import featureOpsC
import JLog
import TempToolbox

# Enable Overwritting Geoprocessing Outputs
arcpy.env.overwriteOutput = True

# GLOBAL VARIABLE DEFINITION
L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Delete=True) # PrintLog
A = None # Stand in for global class definition
mxd = arcpy.mapping.MapDocument('CURRENT')

# define install folder path
install_folder = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]

# FUNCTION DEFINITIONS

def CenterMarker():
    global A
    if A is None:
        A = featureOpsC.Main()
    A.center_on_marker()
    return

def ClearFOV():
    global A
    if A is None:
        A = featureOpsC.Main()
    A.ClearLocAndFOV()
    return

def ClearMarker():
    global A
    if A is None:
        A = featureOpsC.Main()
    A.ClearMarker()
    return

def UndoChange():
    global A
    if A is None:
        A = featureOpsC.Main()
    A.UndoChange()
    return

def EditParameters():
    return

def Export():
    global mxd
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=0)
    if arcpy.Exists(mxd.filePath) == True:
        L.Wrap("Attempting to save the changes to the current map document...")
        mxd.save()
        L.Wrap("Successfully saved the current map")
    import exportWithMods
    E = exportWithMods.ExportWithSub(MXD=None)
    E()
    return

def Marker2Direction():
    global A
    if A is None:
        A = featureOpsC.Main()
    A.bearing_to_marker()
    return

def Marker2Location():
    global A
    if A is None:
        A = featureOpsC.Main()
    A.marker_to_location()
    return

def Marker2Distance():
    global A
    if A is None:
        A = featureOpsC.Main()
    A.distance_to_marker()
    return

def ModifyProject():
    # Execute Main Function
    Toolbox = install_folder + r'\Python Scripts\Toolbox.pyt'
    ToolName = 'ModifyProject'
    TempToolbox.GPToolDialog(Toolbox, ToolName)
    return

def NewMarker(x, y):
    global A
    if A is None:
        A = featureOpsC.Main()
    A.WriteMarkerPoint(x, y)
    return

def NewProject():
    # Execute Main Function
    Toolbox = install_folder + r'\Python Scripts\Toolbox.pyt'
    ToolName = 'NewProject'
    TempToolbox.GPToolDialog(Toolbox, ToolName)
    return

def Next():
    global mxd
    # Local Variables
    PageCount = mxd.dataDrivenPages.pageCount
    CurrentPage = mxd.dataDrivenPages.currentPageID
    # Check if we are on the last page
    if int(CurrentPage) == int(PageCount):
        return
    try:
        # Change Page
        mxd.dataDrivenPages.currentPageID = (CurrentPage + 1)
        return
    except Exception as F:
        print str(F)
        return

def Previous():
    global mxd
    # Local Variables
    PageCount = mxd.dataDrivenPages.pageCount
    CurrentPage = mxd.dataDrivenPages.currentPageID
    # Check if we are on the first page
    if int(CurrentPage) < 2:
        return
    try:
        # Change Page
        mxd.dataDrivenPages.currentPageID = (CurrentPage - 1)
        return
    except Exception as F:
        print str(F)
        return

def Refresh():
    # Global Variables
    global A
    # Check for global class instance
    if A is None:
        # Create global class instance
        A = featureOpsC.Main()
    # Re-calculate Active Point and FOV
    A.Refresh()
    return

def ShowFOV():
    # Global Variables
    global A
    # Refresh Point and FOV
    if A is None:
        A = featureOpsC.Main()
    A.ClearLocAndFOV()
    A.AddLayers()
    A.Refresh()
    return

def ClearMem():
    # Global Variables
    global A
    if A is not None:
        del A
        A = None
    return

def gpxGeotag():
    return

def PosnPnt2geoTag():
    # Execute Main Function
    Toolbox = install_folder + r'\Python Scripts\Toolbox.pyt'
    ToolName = 'SyncTrimblePositions'
    TempToolbox.GPToolDialog(Toolbox, ToolName)
    return

def getOrientation():
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    return A.Orientation

def getHeading():
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    return A.Heading

def getScale():
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    return A.ViewHeight

def getDistance():
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    return A.MetersOfView

def getDescription():
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    return A.Comment

def setOrientation(value):
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    A.setOrientation(value)
    return

def setHeading(value):
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    A.setHeading(value)
    return

def setScale(value):
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    A.setScale(value)
    return

def setDistance(value):
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    A.setDistance(value)
    return

def setDescription(value):
    # Global Variables
    global A
    if A is None:
        A = featureOpsC.Main()
    A.setDescription(value)
    return

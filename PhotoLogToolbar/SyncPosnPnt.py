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
##          SyncPosnPnt.py          ##
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
import importlib
import arcpy

# Import Custom Modules
import JLog
import executables
import timeZones
import tkInputPrompt

# Create PrintLog Class
L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt")

# Enable Overwritting Geoprocessing Outputs
L.Wrap('Setting overwriteOutputs to True...')
arcpy.env.overwriteOutput = True


# FUNCTION DEFINITIONS

def Main(PosnPnt, PhotoPoints, hourDiff=0, minuteDiff=0, secondDiff=0):
    Start = time.perf_counter()
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=0)
    pst = timeZones.Pacific()
    # Get rows from PosnPnt using arcpy.da.SearchCursor()
    PosnPointList = []
    L.Wrap('Getting rows from PosnPnt using arcpy.da.SearchCursor()')
    SearchTime = time.perf_counter()
    # Check for Rcvr_Type field
    desc = arcpy.Describe(PosnPnt)
    fields = desc.fields
    rcvrCol = False
    for field in fields:
        if field.name == 'Rcvr_Type':
            rcvrCol = True
    if rcvrCol is True:
        Rows = arcpy.da.SearchCursor(PosnPnt,["GPS_Date", "GPS_Time", 'SHAPE@Y', 'SHAPE@X', 'Rcvr_Type'])
    if rcvrCol is False:
        Rcvr_Type = tkInputPrompt.RequestReceiver()
        Rows = arcpy.da.SearchCursor(PosnPnt,["GPS_Date", "GPS_Time", 'SHAPE@Y', 'SHAPE@X'])
    for row in Rows:
        # Get Raw Values
        GPS_Date = row[0]
        GPS_Time = row[1]
        Latitude = row[2]
        Longitude = row[3]
        if rcvrCol is True:
            Rcvr_Type = row[4]
        if Rcvr_Type == 'Pro 6T':
            Rcvr_Type = 'Trimble Pro 6T'
        # Convert Values
        Year = GPS_Date.year
        Month = GPS_Date.month
        Day = int(GPS_Date.day)
        Hour = int(GPS_Time[:2]) + int(hourDiff)
        # Convert Hour to 24-Hour format
        if GPS_Time.endswith("pm") or GPS_Time.endswith("PM"):
            if Hour < 12:
                Hour = Hour + 12
        Minute = int(GPS_Time[3:5]) + int(minuteDiff)
        Second =int( GPS_Time[6:8]) + int(secondDiff)
        # this is a hack.  Later this should be replaced with a DateTime-based change, so the problem never happens in the first place, and so the
        if Second > 59:
            Second = Second - 60
            Minute = Minute + 1
        if Second < 0:
            Second = 60 + Second
            Minute = Minute - 1
        if Minute > 59:
            Minute = Minute - 60
            Hour = Hour + 1
        if Minute < 0:
            Minute = 60 + Minute
            Hour = Hour - 1
        # Convert to DateTime
        pdt = datetime(int(Year), int(Month), int(Day), int(Hour), int(Minute), int(Second), tzinfo=pst)
##            udt = (pdt - pdt.utcoffset()).replace(tzinfo=None)
        PosnPointList.append((pdt, Latitude, Longitude, Rcvr_Type))
    del Rows
    # Get rows from PhotoPoints using arcpy.da.SearchCursor()
    L.Time(SearchTime,'Getting PosnPnt rows')
    L.Wrap('Getting rows from PhotoPoints using arcpy.da.UpdateCursor()')
    with arcpy.da.UpdateCursor(PhotoPoints,['SHAPE@X', 'SHAPE@Y', 'Date', 'Time', 'POINT_X', 'POINT_Y', 'LocationSource', 'Asterisk']) as cursor:
        for row in cursor:
            # Get Raw Values
            Year = row[2].year
            Month = row[2].month
            Day = row[2].day
            Hour = row[3].hour
            Minute = row[3].minute
            Second = row[3].second
            pdt = datetime(int(Year), int(Month), int(Day), int(Hour), int(Minute), int(Second), tzinfo=pst)
            BestDiff = 11
            for item in PosnPointList:
                Diff = abs((item[0]-pdt).total_seconds())
                if Diff < BestDiff:
                    BestDiff = Diff
            for item in PosnPointList:
                Diff = abs((item[0]-pdt).total_seconds())
                if Diff == BestDiff:
                    L.Wrap('Time difference = ' + str(Diff))
                    row[0] = item[2]
                    row[1] = item[1]
                    row[4] = float(item[2])
                    row[5] = float(item[1])
                    row[6] = item[3]
                    row[7] = ''
                    cursor.updateRow(row)
    L.Time(Start,'Entire process')
    return

if __name__ == '__main__':
    import SyncPosnPnt
    importlib.reload(SyncPosnPnt)
    PosnPnt = r'R:\ORM\2016\201600559 Wheatland\Site Visits\2017-03-03 - Site Visit\GPS Data\Export\e032011a\PosnPnt.shp'
    PhotoPoints = r'R:\ORM\2016\201600559 Wheatland\Site Visits\2017-03-03 - Site Visit\Mapped Photo Log\GIS_Data.gdb\PhotoPoints'
    SyncPosnPnt.Main(PosnPnt,PhotoPoints,hourDiff=-1,minuteDiff=0,secondDiff=0)

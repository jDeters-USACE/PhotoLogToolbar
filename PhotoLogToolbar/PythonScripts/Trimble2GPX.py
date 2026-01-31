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
##          Trimble2GPX.py          ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  17-Oct-2017   ##
##  ------------------------------- ##
######################################

# Import Built-In Libraries
import arcpy
import os
import math
import sys
import shutil
import time

# Import Custom Modules
import JLog
import executables

# Create PrintLog Class
L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt")

# Enable Overwritting Geoprocessing Outputs
L.Wrap('Setting overwriteOutputs to True...')
arcpy.env.overwriteOutput = True

# Function Definitions



from datetime import timedelta, datetime, tzinfo

class PST(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-8) + self.dst(dt)
    def dst(self, dt):
        # DST starts last Sunday in March
        d = datetime(dt.year, 3, 1)  
        self.dston = d + timedelta(days=6-d.weekday()+7)
        # DST ends last Sunday in October
        d = datetime(dt.year, 11, 1)
        self.dstoff = d + timedelta(days=6-d.weekday())
        if self.dston <=  dt.replace(tzinfo=None) < self.dstoff:
            return timedelta(hours=1)
        else:
            return timedelta(0)
    def tzname(self,dt):
        return "PST -8"

def Main(SHPpath, GPXpath):
    Start = time.perf_counter()
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=0)
    gpx = JLog.PrintLog(Delete=True,Log=GPXpath,Width=900,LogOnly=True)
    L.Wrap('---Start of Trimble2GPX.WriteGPX()---')
    # Write XML Header
    L.Wrap('Writing XML header...')
    gpx.Wrap('<?xml version="1.0" encoding="UTF-8"?>')
    # Write GPX start Tag
    L.Wrap('Writing GPX start Tag...')
    gpx.Wrap('<gpx version="1.0">')
    # Writing name element
    L.Wrap('Writing name element...')
    gpx.SetIndent(4)
    gpx.Wrap('<name>SHP2GPX</name>')
    # Write Track Start Tag with Name and Number elements and Track Segment Start Tag
    L.Wrap('Write Track Start Tag with Name and Number elements and Track Segment Start Tag...')
    gpx.Wrap('<trk><name>Converted Track</name><number>1</number><trkseg>')
    # Get rows from SHPpath using arcpy.da.SearchCursor()
    L.Wrap('Getting rows from SHPpath using arcpy.da.SearchCursor()')
    Rows = arcpy.da.SearchCursor(SHPpath,["GPS_Date","GPS_Time","GNSS_Heigh","Latitude","Longitude"])
    # Write track segment rows
    gpx.SetIndent(8)
    L.Wrap('For each row of the selected feature class, writing <trkpt lat="{1}" lon="{1}"><ele>{2}</ele><time>{3}-{4}-{5}T{6}:{7}:{8}Z</time></trkpt>.format(Latitude,Longitude,Elevation,Year,Month,Day,Hour,Minute,Second)...')
    for row in Rows:
        # Get Raw Values
        GPS_Date = row[0]
        GPS_Time = row[1]
        Elevation = row[2]
        Latitude = row[3]
        Longitude = row[4]
        # Convert Values
        Year = GPS_Date.year
        Month = GPS_Date.month
        Day = int(GPS_Date.day)
        Hour = int(GPS_Time[:2])
        # Get 24-Hour format
        if GPS_Time.endswith("pm") or GPS_Time.endswith("PM"):
            if Hour < 12:
                Hour = Hour + 12
        Minute = GPS_Time[3:5]
        Second = GPS_Time[6:8]
        # Convert to DateTime
        pst = PST()
        pdt = datetime(int(Year),int(Month),int(Day),int(Hour),int(Minute),int(Second),tzinfo=pst)
        udt = (pdt - pdt.utcoffset()).replace(tzinfo=None)
        iso = udt.isoformat() 
        gpx.Wrap('<trkpt lat="{0}" lon="{1}"><ele>{2}</ele><time>{3}Z</time></trkpt>'
                 .format(Latitude,Longitude,Elevation,iso))
    # Write track footer
    gpx.SetIndent(4)
    gpx.Wrap('</trkseg></trk>')
    gpx.SetIndent(0)
    gpx.Wrap('</gpx>')
    return



if __name__ == '__main__':
    L.Wrap('Running test...')
    SHPpath = mainPath + r'\Programming\MyPythonPackages\Mapped_Photo_Log\Test Projects\Stardust\GPS Data\Trimble Export\PosnPnt.shp'
    GPXpath = mainPath + r'\Programming\MyPythonPackages\Mapped_Photo_Log\Test Projects\Stardust\GPS Data\Trimble GPS Track.gpx'    
    Trimble2GPX(SHPpath,GPXpath)
    L.Wrap('Test Complete')

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
##            syncGPX.py            ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

# Import Built-In Libraries
import os
import sys
import time
import datetime

# Import Custom Modules
import JLog
import executables

# Create PrintLog Class
L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt")



def SyncPhotos2GPX(PhotosFolder, GPXpath):
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=3)
    L.Wrap('Using ExifTool.exe to sync Photographs to GPX file')
    C = executables.cmdString()
    C.AddStringInQuotes(r"\\SPK-Netapp1\RDPublic\Personal Folders\Deters\Programming\MyPythonPackages\Other People's Utilities\exiftool\exiftool.exe")
    C.AddString("-geotag")
    C.AddStringInQuotes(GPXpath)
    C.AddStringInQuotes(PhotosFolder)
    C.Execute()
    L.Wrap('Suceeded')
    return

if __name__ == '__main__':
    PhotosFolder = r'R:\ORM\2015\201500538\2016-11-29 - Site Visit\Photographs'
    GPXpath = r'R:\ORM\2015\201500538\2016-11-29 - Site Visit\GPS Data\QStarz\2016-11-29 - Tessie Place QStarz Track.gpx'
    SyncPhotos2GPX(PhotosFolder,GPXpath)
                   

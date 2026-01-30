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
##          SetPyOrPyW.py           ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

### Set Multiprocessing executable


import multiprocessing
import time
import os

# import custom modules
import JLog



versions = ['3']


def SetToPythonW():
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=9)
    L.Wrap(" ")
    L.Wrap("----------Start of SetPyOrPyW.SetToPythonW()-----------")
    L.Wrap(str(time.ctime()))
    for ver in versions:
        path = f"C:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py{ver}/python.exe"
        path = "C:/Python27/ArcGIS" + ver + "/pythonw.exe"
        test = os.path.exists(path)
        if test:
            latest_path = path
            latest_version = ver
    L.Wrap("ArcGIS " + latest_version + " installed on the system...")
    L.Wrap("Setting multiprocessing executable to pythonw.exe")
    multiprocessing.set_executable(latest_path)
    L.Wrap(latest_path)
    L.Wrap("-----------End of SetPyOrPyW.SetToPythonW()------------")
    L.Wrap(" ")
    return latest_path


def SetToPython():
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=9)
    L.Wrap(" ")
    L.Wrap("----------Start of SetPyOrPyW.SetToPython()-----------")
    L.Wrap(str(time.ctime()))
    for ver in versions:
        path = "C:/Python27/ArcGIS" + ver + "/python.exe"
        test = os.path.exists(path)
        if test:
            latest_path = path
            latest_version = ver
    L.Wrap("ArcGIS " + latest_version + " installed on the system...")
    L.Wrap("Setting multiprocessing executable to pythonw.exe")
    multiprocessing.set_executable(latest_path)
    L.Wrap(latest_path)
    L.Wrap("-----------End of SetPyOrPyW.SetToPython()------------")
    L.Wrap(" ")
    return latest_path


if __name__ == '__main__':
    W = SetToPythonW()
    print W
    P = SetToPython()
    print P

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
##             JLog.py              ##
##  ------------------------------- ##
##    Written by: Jason Deters      ##
##  ------------------------------- ##
##   Last Edited on: 22-Jan-2026    ##
##  ------------------------------- ##
######################################


import sys
import os
import stat
import time
import shutil
import textwrap
import subprocess
import traceback


# Function Definitions

def ensure_dir(folder):
    """Ensures entire directory structure given exists"""
    try:
        os.makedirs(folder)
    except Exception:
        pass
# End of ensure_dir function


if os.path.split(sys.executable)[1] == "ArcMap.exe":
    import arcpy

def deleteReadOnly(filePath):
    try:
        os.remove(filePath)
    except Exception:
        try:
            os.chmod(filePath, stat.S_IWRITE)
            os.remove(filePath)
        except Exception:
            raise

#-------------------------------------Class Definitions-----------------------------------#

class PrintLog(object):
    def __init__(self,
                 Delete=False,
                 Log="C:\\Temp\\PhotoLogToolbar_LOG.txt",
                 Indent=0,
                 Width=119,
                 LogOnly=False,
                 ArcPy=False):
        self.Wrapper = textwrap.TextWrapper()
        self.Log = Log
        self.SetIndent(Indent)
        self.SetWidth(Width)
        self.LogOnly = LogOnly
        self.ArcPy = ArcPy
        self.Executable = os.path.split(sys.executable)[1]
        self.prevMsgLen = None
        if self.Log is not None:
            # Get folder portion of log file path
            logPath = os.path.split(Log)[0]
            # Ensure log file folder exists
            ensure_dir(logPath)
            if Delete == True:
                # Attempt to delete log file
                try:
                    deleteReadOnly(self.Log)
                except Exception:
                    pass
    def SetIndent(self,Spaces):
        if type(Spaces) == int:
            InitialIndent = " " * Spaces
            SubIndent = " " * (Spaces+2)
        if type(Spaces) == str:
            InitialIndent = Spaces
            SubIndent = Spaces + "  "
        self.Wrapper.initial_indent = InitialIndent
        self.Wrapper.subsequent_indent = SubIndent
        return
    def SetWidth(self,Width):
        self.Wrapper.width = Width
        return
    def SetLogOnly(self,Boolean):
        self.LogOnly = Boolean
        return
    def Write(self,Message):
        # Ensure we completely overwrite any '\r' lines
        if self.prevMsgLen is not None:
            while len(Message) < self.prevMsgLen:
                Message = u'{0} '.format(Message)
            self.prevMsgLen = None
        if self.Log is not None:
            try:
                with open(self.Log, "a") as f:
                    # Write Message to Log
                    f.write(u"{0}\n".format(Message))
                    tries = 0
                if self.LogOnly == True:
                    return
            except:
                self.Wrap('-------------------------------------------------------')
                self.Wrap('EXCEPTION:')
                self.Wrap(traceback.format_exc())
                self.Wrap('-------------------------------------------------------')
        # Print Message in Python Window, if open
        try:
            print(Message)
        except Exception:
            self.Wrap('-------------------------------------------------------')
            self.Wrap('EXCEPTION:')
            self.Wrap(traceback.format_exc())
            self.Wrap('-------------------------------------------------------')
        # Print Message in ArcMap, if Geoprocessing window is open
        if self.Executable == "ArcGISPro.exe":
            try:
                import arcpy
                arcpy.AddMessage(Message)
            except Exception:
                self.Wrap('-------------------------------------------------------')
                self.Wrap('EXCEPTION:')
                self.Wrap(traceback.format_exc())
                self.Wrap('-------------------------------------------------------')
        return
    def Wrap(self,Message):
        # Local Variable definitions
        ListOfSplitLinesLists = []
        ListOfWrappedStrings = []
        # Skip wrapping for " " Messages
        if Message == " ":
            self.Write(Message)
            return
        if Message == "":
            self.Write(Message)
            return
        # Convert message from types that cause errors with .splitlines()
        if str(type(Message)).startswith("<type 'exceptions."):
            Message = str(Message)
        if type(Message) == type(None):
            Message = str(Message)
        if type(Message) == bool:
            Message = str(Message)
        if type(Message) == int:
            Message = str(Message)
        if type(Message) == float:
            Message = str(Message)
        # Determine how to handle message
        if (type(Message) != list and type(Message) != tuple):
            # Split lines indicated by /n into a list of separate strings
            SplitLinesList = Message.splitlines()
            # Append new list of lines into the ListOfSplitLinesLists
            ListOfSplitLinesLists.append(SplitLinesList)
        else:
            # Iterate over a list object
            for item in Message:
                # Split lines indicated by /n into a list of separate strings
                SplitLinesList = item.splitlines()
                # Append new list of lines into the ListOfSplitLinesLists
                ListOfSplitLinesLists.append(SplitLinesList)
                del SplitLinesList
        # Iterate over a list of lists (ListOfSplitLines)
        for SplitLinesList in ListOfSplitLinesLists:
            # Iterate over the sub-list
            for Line in SplitLinesList:
                # Wrap all individual lines, which creates a new list
                WrappedLinesList = self.Wrapper.wrap(Line)
                for WrappedLine in WrappedLinesList:
                    self.Write(WrappedLine)
        return
    def Time(self,StartTime,Task):
        Time = time.perf_counter() - StartTime
        if Time < 61:
            Seconds = str(int(Time))
            self.Wrap(Task + " took " + Seconds + " seconds to complete.")
            self.Wrap("--------------------------------------------------------")
        if Time > 60:
            Minutes = str(int(Time / 60))
            Seconds = str(int(Time - (int(Time / 60) * 60)))
            self.Wrap(Task + " took " + Minutes + " minutes and " + Seconds + " seconds to complete.")
            self.Wrap("--------------------------------------------------------")
        return
    def sendLog(self):
        recipient='Jason.Deters@usace.army.mil'
        subject='Photo Log Toolbar Error Log'
        attachmentPath=self.Log
        outlookpath2doc = None
        for root, directories, filenames in os.walk('C:\\Program Files (x86)\\Microsoft Office'):
            for f in filenames:
                if 'OUTLOOK.EXE' in f:
                    fileName = os.path.join(root,f)
                    outlookpath2doc = '"{}"'.format(fileName)
        if outlookpath2doc is not None:
            outlookpath2doc = '"C:\Program Files (x86)\Microsoft Office\Office15\OUTLOOK.EXE"'
            compose = '/c ipm.note'
            recipients = '/m "{}&subject={}"'.format(recipient,subject)
            attachment = '/a "' + attachmentPath + '"'
            command = ' '.join([outlookpath2doc, compose, recipients, attachment])
            process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
        else:
            print("Microsoft Outlook not found on this machine. Cannot send message.")
    def statusMsg(self,Message):
        if self.Executable != 'pythonw.exe':
            self.prevMsgLen = len(Message)
            print('{0}\r'.format(Message),)
    def deleteLog(self):
        deleteReadOnly(self.Log)
        return
# End of PrintLog Class

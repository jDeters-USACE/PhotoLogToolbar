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
##          tkFilePrompt.py         ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

import os
import Tkinter
from Tkinter import *
import tkSimpleDialog
import ttk
import sys
import multiprocessing
import time
import threading
import thread
import tkInputPrompt
import SetPyOrPyW
import JLog


# NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE #
# Avoid importing any script that imports arcpy or it will take >45 seconds for Tkinter to open
# NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE #

class Minion(multiprocessing.Process):
    def __init__(self, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
    
    def run(self):
        Number = 1
        L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=0)
        File = "C:\\Temp\\SPK LiDAR Tile Index\\ProcessManager_SubProcess_"+str(os.getpid())+".txt"
        proc_name = self.name
        L.Wrap(str(proc_name))
        L.Wrap("--------------------------------------------------------")
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                L.Wrap('Kill Command Recieved - %s: Exiting' % proc_name)
                # Remove references to modified sys files
                self.task_queue.task_done()
                break
            L.Wrap("--------------------------------------------------------")
            L.Wrap(('%s - %s: %s' % (Number, proc_name, next_task)))
            Number = Number + 1
            try:
                answer = next_task()
            except Exception as exception:
                L.Wrap(str(exception))
                Crash = arcpy.GetMessages()
                L.Wrap(str(Crash))
                answer = Crash
            finally:
                self.task_queue.task_done()
                self.result_queue.put(answer)
        return
# End of Minion


class tkName(object):
    def __init__(self):
        pass
    
    def __call__(self):
        root = Tkinter.Tk()
        root.withdraw()
        Name = tkSimpleDialog.askstring("Editor Name",
                                        "Please provide the name of the person editing the photo point",
                                        parent=root)
        root.destroy()
        return Name
    
    def __str__(self):
        return "Create Tkinter UI to Collect User Name"
# End of tkName


def RequestName():
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=0)
    multiprocessing.freeze_support()
    L.Wrap(" ")
    L.Wrap("--------------Start of tkInputPrompt.RequestName()---------------")
    L.Wrap(str(time.ctime()))
    # MULTIPROCESSING
    SetPyOrPyW.SetToPythonW()
    tasks = multiprocessing.JoinableQueue()
    results = multiprocessing.Queue()
    # Create ProgressProcess
    L.Wrap("Creating Progress Minion...")
    ProgressProcess = Minion(tasks, results)
    # Start minion
    L.Wrap("Starting Progress Minion...")
    ### MANDATORY CODE TO DEAL WITH ArcGIS 10.3.1 GLITCH ###
    sys.argv = ['']
    ### MANDATORY CODE TO DEAL WITH ArcGIS 10.3.1 GLITCH ###
        # Glitch states the following:
        # File "C;\Python27\ArcGIS10.3\Lib\multiprocessing\forking.py", line 399, in get_preparation_data
        #     sys_argv=sys.argv,
        # AttributeError: 'module' object has no attribute 'argv'
    ProgressProcess.start()
    L.Wrap("Creating UI class...")
    A = tkName()
    L.Wrap("Sending UI class to Progress Minion...")
    tasks.put(A)
    L.Wrap("Sending Minion Kill Command...")
    tasks.put(None)
    L.Wrap("Waiting for results")
    tasks.join()
    L.Wrap("Getting results...")
    Name = results.get()
    L.Wrap("Name = " + Name)
    L.Wrap("---------------End of ProgressBar.MakeProgressBar()----------------")
    L.Wrap(" ")
    return Name
# end RequestName

if __name__ == '__main__':
    import tkFilePrompt
    a = tkFilePrompt.RequestName()

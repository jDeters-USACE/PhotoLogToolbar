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
##          TempToolbox.py          ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

import os, sys
import glob
import shutil
import tempfile
import threading
import time

import arcpy, pythonaddins
  
def GPToolDialog(toolbox, tool):
    """
         * Workaround for NIM089253 - "TypeError: GPToolDialog() takes at most 1 argument (2 given)
           http://support.esri.com/en/bugs/nimbus/TklNMDg5MjUz
         * Workaround for defaults only refreshing on first run - copy the pyt (and xml docs)
           which forces Arc to reload it every time.
    """
    tmpdir = tempfile.mkdtemp(prefix='toolbox')
    tmpfile = os.path.join(tmpdir,os.path.basename(toolbox))
    docs=glob.glob(toolbox[:-4]+'*.xml')
    shutil.copy(toolbox,tmpdir)
    for doc in docs:shutil.copy(doc,tmpdir)
    try:
        result=pythonaddins.GPToolDialog(tmpfile,tool)
    except TypeError:
        pass
    finally:
        #Give ArcMap time to load the toolbox before it gets cleaned up 
        threading.Thread(target=rm, args = (tmpdir,3)).start()
        return None
  
def rm(d, wait=1):
    time.sleep(wait)
    try:
        shutil.rmtree(d)
    except:
        pass

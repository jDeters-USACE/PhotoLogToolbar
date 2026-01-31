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
##   Photo Log Stand-alone GUI.py   ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

# import standard libraries
import subprocess
import os

# import custom libraries
import SetPyOrPyW
import executables

# find module path
file_path = os.path.dirname(os.path.realpath(__file__))

# define gui file path
GUI_path = file_path + '/pl_GUI.py'

# get 32-bit python path
pyPath = SetPyOrPyW.SetToPython()

# Create cmdString class
cmd = executables.cmdString()

# create command
cmd.AddStringInQuotes(pyPath)
cmd.AddStringInQuotes(GUI_path)

# Execute command
cmd.ExecuteConsole()



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
##         osConvenience.py         ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

# Check for / create a folder. Will also check for / create any subfolders recursively

import os

def ensure_dir(folder):
    """Ensures entire directory structure given exists"""
    try:
        os.makedirs(folder)
    except WindowsError:
        pass
# End of ensure_dir function


##if __name__ == '__main__':
##    import time
##    Start = time.perf_counter()
##    Folder = r'C:\Temp\test\temp\temp\temp\temp\temp\temp\temp\temp\temp\temp\temp\temp\temp\temp'
##    ensure_dir(Folder)
##    Total = time.perf_counter() - Start
##    print "Took ",Total," seconds."

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
##        windowsScaling.py         ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Oct-2017   ##
##  ------------------------------- ##
######################################

import Tkinter

def scalingAt125():
    Window = Tkinter.Tk()
    Window.geometry("500x500+80+80")

    frame = Tkinter.Frame(Window) # this will hold the label
    frame.pack(side = "top")

    # CALCULATE:
    measure = Tkinter.Label(frame, font = ("Purisa", 10), text = "The width of this in pixels is.....", bg = "yellow")
    measure.grid(row = 0, column = 0) # put the label in
    measure.update_idletasks() # this is VERY important, it makes python calculate the width
    width = measure.winfo_width() # get the width
    Window.destroy()
##    print 'String width = {}'.format(width)
    if width > 195:
        scalingSetAt125 = True
    else:
        scalingSetAt125 = False
    return scalingSetAt125

if __name__ == '__main__':
    result = scalingAt125()
    print 'Scaling set to 125% = {}'.format(result)

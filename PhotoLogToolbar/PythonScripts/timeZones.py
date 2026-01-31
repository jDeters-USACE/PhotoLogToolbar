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
##           timeZones.py           ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  20-Jun-2017   ##
##  ------------------------------- ##
######################################

import time
from datetime import timedelta, datetime, tzinfo

ZERO = timedelta(0)

class UTC(tzinfo):
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

class Hawaii(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-10) + self.dst(dt)
    def dst(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return "HST"

class Hawaii_Aleutian(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-10) + self.dst(dt)
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
    def tzname(self, dt):
        if self.dst(dt) == timedelta(0):
            return "HAST"
        if self.dst(dt) == timedelta(hours=1):
            return "HADT"

class Alaska(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-9) + self.dst(dt)
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
    def tzname(self, dt):
        if self.dst(dt) == timedelta(0):
            return "AKST"
        if self.dst(dt) == timedelta(hours=1):
            return "AKDT"

class Pacific(tzinfo):
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
    def tzname(self, dt):
        if self.dst(dt) == timedelta(0):
            return "PST"
        if self.dst(dt) == timedelta(hours=1):
            if time.strftime("%Z") == 'Pacific Daylight Time' or time.strftime('%Z') == 'Pacific Standard Time':
                return "PDT"
            if time.strftime("%Z") == 'US Mountain Standard Time':
                return "MST"

class Mountain(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-7) + self.dst(dt)
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
    def tzname(self, dt):
        if self.dst(dt) == timedelta(0):
            return "MST"
        if self.dst(dt) == timedelta(hours=1):
            return "MDT"

class Arizona(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-7) + self.dst(dt)
    def dst(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return "MST"

class Central(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-6) + self.dst(dt)
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
    def tzname(self, dt):
        if self.dst(dt) == timedelta(0):
            return "CST"
        if self.dst(dt) == timedelta(hours=1):
            return "CDT"

class Eastern(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-5) + self.dst(dt)
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
    def tzname(self, dt):
        if self.dst(dt) == timedelta(0):
            return "EST"
        if self.dst(dt) == timedelta(hours=1):
            return "EDT"

def tzList():
    zoneList = []
    zoneList.append(Hawaii())
    zoneList.append(Alaska())
    zoneList.append(Pacific())
    zoneList.append(Mountain())
    zoneList.append(Central())
    zoneList.append(Eastern())
    return zoneList


if __name__ == '__main__':
    utc = UTC()
    pst = Pacific()
    pdt = datetime(2016,7,26,9,40,15, tzinfo=pst)
    print(pst)
    print(pdt)
    print(pdt.tzname())
    print(pdt.dst())
##    udt = (pdt - pdt.utcoffset()).replace(tzinfo=None)
##    print(udt)
##    udt2 = pdt.astimezone(utc)
##    print(udt2)
    
    print(time.gmtime())
    time.timezone
    print(time.strftime("%z"))
    print(time.strftime("%Z"))
    print("")
#    pTest = Pacific()
#    pTest.tzname(pdt)
#    print(pTest.tzname(pdt))
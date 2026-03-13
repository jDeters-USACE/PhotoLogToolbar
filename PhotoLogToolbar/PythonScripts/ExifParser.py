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
##          ExifParser.py           ##
##  ------------------------------- ##
##     Written by: Jason Deters     ##
##  ------------------------------- ##
##   Last Edited on:  2025-09-04    ##
##  ------------------------------- ##
######################################

# Import Standard Libraries
import os
import sys
import importlib
import time
import math
import shutil
import datetime
import PIL
import PIL.Image as PILimage
from PIL import ImageDraw, ImageFont, ImageEnhance
from PIL.ExifTags import TAGS, GPSTAGS
from dateutil import parser # Pre-installed in ArcGIS Pro
## define install folder path
#install_folder = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
#
## Import PyExifTool
#sys.path.append(install_folder + r"\exiftool\PyExifTool")
#import exiftool

# Import Custom Modules
import JLog
import timeZones

# CLASS DEFINITIONS


class Wrapper(object):

    def __init__(self):
        # Creating Blank PhotoData Element
        self.PhotoData = 'No Metadata Loaded'
        # Create PrintLogger instance
        self.L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=12)
        # Announce initialization
        self.L.Wrap('ExifParser initialized:  No metadata loaded')
        # Create empty values
        self.GPStoTakenDifference = None
        self.ModeOfTimeDifference = None

    @staticmethod
    def get_if_exist(data, key):
        if key in data:
            return data[key]
        return None

    @staticmethod
    def convert_to_degress(value):
        """Helper function to convert the GPS coordinates
        stored in the EXIF to degress in float format"""
        d0 = value[0].numerator
        d1 = value[0].denominator
        d = float(d0) / float(d1)
        m0 = value[1].numerator
        m1 = value[1].denominator
        m = float(m0) / float(m1)
        s0 = value[2].numerator
        s1 = value[2].denominator
        s = float(s0) / float(s1)
        return d + (m / 60.0) + (s / 3600.0)

    def GetMetadata(self, Photo):
        """Attempts to pull and store all metadata from a given photo"""
        self.L.SetIndent(12)
        self.L.Wrap('Getting metadata for '+os.path.split(Photo)[1]+'...')
        self.L.SetIndent(14)
        self.LastOpenedPhotoPath = Photo
        # Open Image File
        img = PIL.Image.open(Photo)
        # Use PIL to access EXIF data
        info = img._getexif()
        # Create Empty Dictionary
        exif_data = {}
        # Add parsed exif_data to empty dictionary
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]
                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
        # Add additional metadata using the OS Library to simulate Phil Harvey's EXIF_TOOL results
        # File Creation Date
        creation_timestamp = os.path.getctime(Photo)
        creation_datetime = datetime.datetime.fromtimestamp(creation_timestamp)
        file_create_date = f'{creation_datetime}{time.strftime("%z")}'
        exif_data['FileCreateDate'] = file_create_date
        # File Last Modified Date
        modification_timestamp = os.path.getmtime(Photo)
        modification_datetime = datetime.datetime.fromtimestamp(modification_timestamp)
        file_modified_date = f'{modification_datetime}{time.strftime("%z")}'
        exif_data['FileModifyDate'] = file_modified_date
        # Store dictionary
        self.PhotoData = exif_data
        # Close image file
        del img
        # Get difference of GPS time and "Taken" Time
        self.GPStoTakenDifference = self.GetTimeDifference()
        return self.PhotoData


    def Camera(self):
        """Join Make and model metadata entries"""
        try:
            Make = self.PhotoData['Make']
        except Exception:
            self.L.Wrap('WARNING: Camera Make not found in metadata!')
            Make = ''
        try:
            Model = self.PhotoData['Model']
        except Exception:
            self.L.Wrap('WARNING: Camera Model not found in metadata!')
            Model = ''
        if Make == '':
            if Model == '':
                Camera = 'Unknown'
            else:
                Camera = Model
        else:
            if Model == '':
                Camera = Make
            else:
                if (Make in Model) is True:
                    Camera = Model
                else:
                    Camera = '{} {}'.format(Make, Model)
        self.L.Wrap('Camera = {}'.format(Camera))
        return Camera

    def LongEdgeFOV(self):
        """Pull FocalLengthIn35mmFilm and calculate LongEdgeFOV"""
        try:
            if self.PhotoData['Make'] == 'Garmin':
                LongEdgeFOV = 73.7397952917
                self.L.Wrap('LongEdgeFOV = ' + str(LongEdgeFOV))
                return LongEdgeFOV
        except Exception:
            pass
        try:
            focal_length = float(self.PhotoData['FocalLength'])
            focal_length_in_35mm = float(self.PhotoData['FocalLengthIn35mmFilm'])
            if focal_length == focal_length_in_35mm:
                focal_length_in_35mm = focal_length * 7.2
                self.L.Wrap('COULD NOT DETERMINE "FocalLengthIn35mmFilm" value.  Field of View estimate may be off!')
            LongEdgeFOV = math.degrees(2*math.atan(float(36)/(float(2)*float(focal_length_in_35mm))))
            self.L.Wrap('LongEdgeFOV = ' + str(LongEdgeFOV))
            return LongEdgeFOV
        except Exception:
            LongEdgeFOV = 22.8673625309
            self.L.Wrap('WARNING: Long Edge Field of View could not be determined. Defaulting to "{}"'.format(LongEdgeFOV))
            return LongEdgeFOV

    def ShortEdgeFOV(self):
        """Pull FocalLengthIn35mmFilm and calculate ShortEdgeFOV"""
        try:
            if self.PhotoData['EXIF:Make'] == 'Garmin':
                ShortEdgeFOV = 53.1301023542
                self.L.Wrap('ShortEdgeFOV = ' + str(ShortEdgeFOV))
                return ShortEdgeFOV
        except Exception:
            pass
        try:
            focal_length = float(self.PhotoData['FocalLength'])
            focal_length_in_35mm = float(self.PhotoData['FocalLengthIn35mmFilm'])
            if focal_length == focal_length_in_35mm:
                focal_length_in_35mm = focal_length * 7.2
                self.L.Wrap('COULD NOT DETERMINE "FocalLengthIn35mmFilm" value.  Field of View estimate may be off!')
            ShortEdgeFOV = math.degrees(2*math.atan(float(24)/(float(2)*float(focal_length_in_35mm))))
            self.L.Wrap('ShortEdgeFOV = ' + str(ShortEdgeFOV))
            return ShortEdgeFOV
        except Exception:
            ShortEdgeFOV = 15.3579276147
            self.L.Wrap('WARNING: Short Edge Field of View could not be determined. Defaulting to "{}"'.format(ShortEdgeFOV))
            return ShortEdgeFOV

    def AspectRatio(self):
        """Find and then divide the short-edge resolution by the long-edge resolution"""
        try:
            # Create List of Photo Dimensions
            Dimensions = [float(self.PhotoData['ExifImageHeight']), float(self.PhotoData['ExifImageWidth'])]
            # Calculate Aspect Ratio
            AspectRatio = min(Dimensions)/max(Dimensions)
            self.L.Wrap('AspectRatio = ' + str(AspectRatio))
            return AspectRatio
        except Exception:
            AspectRatio = 0.5625
            self.L.Wrap('WARNING: Aspect Ratio could not be determined. Defaulting to "{}"'.format(AspectRatio))
            return AspectRatio

    def Orientation(self):
        """Determine the long edge and make an orientation assumption"""
        try:
            if float(self.PhotoData['ExifImageHeight']) < float(self.PhotoData['ExifImageWidth']):
                Orientation = "Landscape"
            else:
                Orientation = "Portrait"
            self.L.Wrap('Orientation = ' + Orientation)
            return Orientation
        except Exception:
            Orientation = "Landscape"
            self.L.Wrap('WARNING: Orientation could not be determined. Defaulting to "{}"'.format(Orientation))
            return Orientation

    def GetTimeZone(self):
        try:
            # Get photo created date timezone offset tag
            createdOffset = f"{self.PhotoData['FileCreateDate'][-5:][:3]}:{self.PhotoData['FileCreateDate'][-5:][3:]}"
            # Compare to other timezones
            zones = timeZones.tzList()
            for tz in zones:
                # create datetime in the given timezone to test if photo's offset matches offset on the photo date (to account for DST)
                try:
                    # This is the way to do it, but for a certain number of cases, DateTimeOriginal doens't exist
                    tzt = datetime.datetime.strptime(self.PhotoData['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S').replace(tzinfo=tz)
                except:
                    # This could be accurate, but it gets changed when files are copied sometimes.
                    tzt = datetime.datetime.strptime(self.PhotoData['FileCreateDate'][:-6], '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=tz)
                # truncate only the offset tag
                tztOffset = str(tzt)[-6:]
                # compare file offset and current tz offset
                if createdOffset == tztOffset:
                    # tz matches file created date, returning timezone
                    tz_name = tzt.tzname()
                    self.L.Wrap('Timezone = ' + str(tz_name))
                    return tz, tz_name
        except Exception:
            self.L.Wrap('No FileCreateDate found for this photo')
            return None, None

    def GetGPSDateTime(self):
        """
        Helper function to convert the GPS Timestamp stored in the EXIF to HH:MM:SS
        """
        try:
            utc = timeZones.UTC()
            # GPSTimeStamp is a tuple of tuples: ((h_num, h_den), (m_num, m_den), (s_num, s_den))
            h, m, s = self.PhotoData['GPSInfo']['GPSTimeStamp']
            # Get GPS Timestamp in hours Minutes Seconds
            hour = h.numerator / h.denominator
            minute = m.numerator / m.denominator
            second = s.numerator / s.denominator
            # Get GPS Date Stamp
            gps_date_stamp = self.PhotoData['GPSInfo']['GPSDateStamp']
            # Calculate Datetime
            if int(second) < second:
                gps_datetime_utm = datetime.datetime.strptime(f'{gps_date_stamp} {int(hour)}:{int(minute)}:{second}', '%Y:%m:%d %H:%M:%S.%f').replace(tzinfo=utc)
            else:
                gps_datetime_utm = datetime.datetime.strptime(f'{gps_date_stamp} {int(hour)}:{int(minute)}:{int(second)}', '%Y:%m:%d %H:%M:%S').replace(tzinfo=utc)
            return gps_datetime_utm
        except Exception:
            self.L.Wrap('No GPS DateTime found for this photo')
            return None

    def GetTimeDifference(self):
        tz = self.GetTimeZone()[0]
        try:
            GPSutc = self.GetGPSDateTime()
            GPStz = GPSutc.astimezone(tz)
            self.L.Wrap('GPS Time:    ' + str(GPStz))
            try:
                TAKENtz = datetime.datetime.strptime(self.PhotoData['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S').replace(tzinfo=tz)
            except Exception:
                TAKENtz = datetime.datetime.strptime(self.PhotoData['FileCreateDate'][:-6], '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=tz)
            self.L.Wrap('Camera Time: ' + str(TAKENtz))
            self.GPStoTakenDifference = TAKENtz - GPStz
            self.L.Wrap('GPStoTakenDifference: ' + str(self.GPStoTakenDifference))
            return self.GPStoTakenDifference
        except Exception:
            self.L.Wrap('No GPS DateTime found for this photo')
            return None

    def GetModeOfTimeDifferences(self, images):
        diffs = []
        bestCount = 0
        bestDiff = None
        for I in images:
            self.GetMetadata(I)
            diff = self.GPStoTakenDifference
            if diff is not None:
                bestDiff = diff
            diffs.append(diff)
        n = 0
        self.L.SetIndent(12)
        self.L.Wrap('Searching for the Mode of the time differences...')
        self.L.SetIndent(14)
        diffSet = set(diffs)
        for d in diffSet:
            if d is not None:
                thisCount = 0
                for od in diffs:
                    test = str(d) == str(od)
##                    self.L.Wrap(str(d)+' == '+str(od)+' = '+str(test))
                    if str(d) == str(od):
                        thisCount += 1
                if thisCount >= bestCount:
                    bestCount = thisCount
                    bestDiff = d
                self.L.Wrap(str(thisCount) + ' occurrences of ' + str(d))
        self.L.Wrap('GPStoTakenDifference Mode: ' + str(bestDiff))
        self.ModeOfTimeDifference = bestDiff
        return self.ModeOfTimeDifference

    def Date(self):
        """Pull DateTimeOriginal from metadata and split to return just the date"""
        try:
            if self.GPStoTakenDifference is not None:
                TAKEN = datetime.datetime.strptime(self.PhotoData['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
                s = str(TAKEN - self.GPStoTakenDifference)[:10]
                Date = datetime.datetime(int(s[:4]), int(s[5:7]), int(s[8:10]))
                self.L.Wrap('Date = ' + str(Date) + ' - (Corrected with individual GPS Time offset)')
                return Date
            elif self.ModeOfTimeDifference is not None:
                TAKEN = datetime.datetime.strptime(self.PhotoData['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
                s = str(TAKEN - self.ModeOfTimeDifference)[:10]
                Date = datetime.datetime(int(s[:4]), int(s[5:7]), int(s[8:10]))
                self.L.Wrap('Date = ' + str(Date) + ' - (Corrected with Mode of GPS Time offsets)')
                return Date
            else:
                try:
                    s = str(self.PhotoData['DateTimeOriginal'][:10])
                    Date = datetime.datetime(int(s[:4]), int(s[5:7]), int(s[8:10]))
                except Exception:
                    s = str(self.PhotoData['FileModifyDate'][:10])
                    Date = datetime.datetime(int(s[:4]), int(s[5:7]), int(s[8:10]))
                self.L.Wrap('Date = ' + str(Date) + ' - (No GPS Time Correction)')
                return Date
        except Exception:
            raise

    def Time(self):
        """Pull DateTimeOriginal from metadata and split to return just the time"""
        try:
            if self.GPStoTakenDifference is not None:
                TAKEN = datetime.datetime.strptime(self.PhotoData['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
                Time = str(TAKEN - self.GPStoTakenDifference)[11:19]
                self.L.Wrap('Time = ' + Time + ' - (Corrected with individual GPS Time offset)')
                return Time
            if self.ModeOfTimeDifference is not None:
                TAKEN = datetime.datetime.strptime(self.PhotoData['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
                Time = str(TAKEN - self.ModeOfTimeDifference)[11:19]
                self.L.Wrap('Time = ' + Time + ' - (Corrected with Mode of GPS Time offsets)')
                return Time
            else:
                try:
                    Time = str(self.PhotoData['DateTimeOriginal'][11:19])
                except Exception:
                    Time = str(self.PhotoData['FileModifyDate'][11:19])
                self.L.Wrap('Time = ' + Time + ' - (No GPS Time Correction)')
                return Time
        except Exception:
            raise

    def X_Coord(self):
        """Pull X value using GPSLongitude"""
        try:
            X = self.convert_to_degress(self.PhotoData['GPSInfo']['GPSLongitude'])
            Ref = self.PhotoData['GPSInfo']['GPSLongitudeRef']
            if Ref == 'W':
                X = f"-{X}"
            self.L.Wrap('X = ' + str(X))
            return X
        except Exception:
            X = 0
            self.L.Wrap("NO GPS DATA PROVIDED FOR THIS PHOTOGRAPH, SETTING TO 0,0")
            return X

    def Y_Coord(self):
        """Pull Y value using GPSLatitude"""
        try:
            Y = self.convert_to_degress(self.PhotoData['GPSInfo']['GPSLatitude'])
            self.L.Wrap('Y = ' + str(Y))
            return Y
        except Exception:
            Y = 0
            self.L.Wrap("NO GPS DATA PROVIDED FOR THIS PHOTOGRAPH, SETTING TO 0,0")
            return Y

    def Heading(self):
        """Pull heading from XMP:GPSImgDirection"""
        try:
            Heading = self.PhotoData['GPSInfo']['GPSImgDirection']
            self.L.Wrap('Heading = ' + str(Heading))
            return Heading
        except Exception:
            return ""

    def ListAllAttributes(self):
        """List all available metadata Keywords and values for development purposes"""
        try:
            self.L.SetIndent(0)
            self.L.Wrap('Listing all attributes...')
            self.L.Wrap('  #-------File-------#')
            for item in self.PhotoData:
                if str(item).startswith('File'):
                    self.L.Wrap(str(item) + ' ' + str(self.PhotoData[str(item)]))
            self.L.Wrap('')
            self.L.Wrap('  #-------EXIF-------#')
            for item in self.PhotoData:
                if str(item).startswith('EXIF'):
                    self.L.Wrap(str(item) + ' ' + str(self.PhotoData[str(item)]))
            self.L.Wrap('')
            self.L.Wrap('  #-------XMP-------#')
            for item in self.PhotoData:
                if str(item).startswith('XMP'):
                    self.L.Wrap(str(item) + ' ' + str(self.PhotoData[str(item)]))
            self.L.Wrap('')
            self.L.Wrap('  #-------MakerNotes-------#')
            for item in self.PhotoData:
                if str(item).startswith('MakerNotes'):
                    self.L.Wrap(str(item) + ' ' + str(self.PhotoData[str(item)]))
            self.L.Wrap('')
            self.L.Wrap('  #-------Composite-------#')
            for item in self.PhotoData:
                if str(item).startswith('Composite'):
                    self.L.Wrap(str(item) + ' ' + str(self.PhotoData[str(item)]))
            self.L.Wrap('')
            self.L.Wrap('  #-------Other Metadata-------#')
            for item in self.PhotoData:
                if str(item).startswith('File'):
                    pass
                elif str(item).startswith('EXIF'):
                    pass
                elif str(item).startswith('XMP'):
                    pass
                elif str(item).startswith('MakerNotes'):
                    pass
                elif str(item).startswith('Composite'):
                    pass
                else:
                    self.L.Wrap(str(item) + ' ' + str(self.PhotoData[str(item)]))
            self.L.Wrap('')
            self.L.SetIndent(13)
        except Exception:
            raise
# End of PyExifToolWrapper Class

if __name__ == '__main__':
#    PhotoFolder = r'R:\Code\ArcMap Extensions\Photo-LogToolbar\Test Projects\201500644 - Stewart Water Diversion\2016-06-14 - Site Visit\Photographs'
    PhotoFolder = r'C:\Users\L2RCSJ9D\OneDrive - US Army Corps of Engineers\Documents\ArcGIS\Projects\PhotoLogToolbar\Test Projects\201500644 - Stewart Water Diversion\2016-06-14 - Site Visit\Photographs'
    images = filter(lambda x: x.lower().endswith(('.jpg', '.jpeg', '.png', '.tif')), os.listdir(PhotoFolder))
    photo_paths = []
    exclude_list = ['(R090)', '(R180)', '(R270)']
    for name in images:
        excluded = False
        for exclude_string in exclude_list:
            if exclude_string in name:
                excluded = True
        if excluded is False:
            photo_paths.append(PhotoFolder + '\\' + name)
    ET = Wrapper()
    ET.GetModeOfTimeDifferences(photo_paths)
    for Photo in photo_paths:
        print("")
        print("")
        print("")
        ET.GetMetadata(Photo)
        ET.X_Coord()
        ET.Y_Coord()
        ET.Date()
        ET.Time()
        ET.Heading()
        ET.Orientation()
        ET.Camera()
        ET.LongEdgeFOV()
        ET.ShortEdgeFOV()
        ET.AspectRatio()
        ET.GetTimeDifference()
        ET.GetTimeZone()
##        ET.ListAllAttributes()
##    raw_input("test")

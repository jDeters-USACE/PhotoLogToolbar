

def setOrientation(self, value):
    self.SelectCurrentImage()
    newPath = None
    if value == u"Rotate 90\xb0 CW":
        L.Wrap('Rotate 90 Degrees selected...')
        currentPath = self.PhotoPath
        currentPathNoExt, ext = os.path.splitext(currentPath)
        currentEnd = currentPathNoExt[-6:]
        L.Wrap('CurrentPath = ' + currentPath)
        endList = ['(R090)', '(R180)', '(R270)']
        if not currentEnd in endList:
            L.Wrap('First rotation')
            pathR090 = currentPathNoExt + '(R090)' + ext
            if not os.path.exists(pathR090):
                arcpy.env.addOutputsToMap = False
                arcpy.Rotate_management(currentPath, pathR090, "90")
                arcpy.env.addOutputsToMap = True
            newPath = pathR090
        if currentEnd == '(R090)':
            L.Wrap('Second rotation')
            pathR180 = currentPathNoExt[:-6] + '(R180)' + ext
            if not os.path.exists(pathR180):
                arcpy.env.addOutputsToMap = False
                arcpy.Rotate_management(currentPath, pathR180, "90")
                arcpy.env.addOutputsToMap = True
            newPath = pathR180
        elif currentEnd == '(R180)':
            L.Wrap('Third rotation')
            pathR270 = currentPathNoExt[:-6] + '(R270)' + ext
            if not os.path.exists(pathR270):
                arcpy.env.addOutputsToMap = False
                arcpy.Rotate_management(currentPath, pathR270, "90")
                arcpy.env.addOutputsToMap = True
            newPath = pathR270
        elif currentEnd == '(R270)':
            L.Wrap('Fourth rotation')
            newPath = currentPathNoExt[:-6] + ext
        L.Wrap('newPath = ' + newPath)
##            # Get updated orientation using ExifTool
##            L.Wrap('Creating instance of PyExifToolWrap to get updated Orientation...')
##            ET = PyExifToolWrap.Wrapper()
##            ET.GetMetadata(newPath)
##            newOrientation = ET.Orientation()
##            L.Wrap('Terminating PyExifToolWrapper class...')
##            ET.Terminate()
##            del ET
        L.Wrap('Updating fields in PhotoPoints feature class...')
        with arcpy.da.UpdateCursor(self.PhotoPoints, ['Orientation', 'PhotoPath']) as cursor:
            for row in cursor:
                if row[0] == 'Landscape':
                    newOrientation = 'Portrait'
                else:
                    newOrientation = 'Landscape'
                row[0] = newOrientation
                row[1] = newPath
                cursor.updateRow(row)
        L.Wrap('Field update complete.')
    else:
        with arcpy.da.UpdateCursor(self.PhotoPoints, ['Orientation']) as cursor:
            for row in cursor:
                row[0] = value
                cursor.updateRow(row)
    self.Refresh()
    return
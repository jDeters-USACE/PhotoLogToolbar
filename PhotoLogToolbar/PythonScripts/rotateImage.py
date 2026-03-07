import os
import arcpy

import JLog
import fovUpdater

def Main(CurrentPhoto=True):
    CurrentPhoto=True # Always, for this one
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=2)
    # Reference the project currently open in ArcGIS Pro
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    # Get the active view
    active_view = aprx.activeView
    # Check if the active view is a layout
    if active_view is not None and hasattr(active_view, "pageHeight"):
        # Set the active_layout to the current active_view
        active_layout = active_view
        # Get Map Series Object from the active_layout
        ms = active_layout.mapSeries

        # Get Main Map Frame
        for mf in active_layout.listElements("MAPFRAME_ELEMENT"):
            if "Photo Log - Main" in mf.map.name:

                # Get Photo Location Layer
                for lyr in mf.map.listLayers():
                    if "Photo Location" in lyr.name:
                        # Define Feature Class
                        fcPhotoPoints = lyr.dataSource

                        # Determine Where Clause
                        if CurrentPhoto:
                            # Get the current page's OID - ms.pageRow provides the attribute row of the current page index
                            current_oid = ms.pageRow.OBJECTID 
                            # Get the OID field name
                            oid_field = arcpy.Describe(fcPhotoPoints).OIDFieldName
                            # reate a Where Clause to target ONLY this row
                            where = f"{oid_field} = {current_oid}"
                        else:
                            where = None

                        # Get current Photo Location Shape object
                        with arcpy.da.SearchCursor(fcPhotoPoints, ['PhotoPath'], where_clause=where) as search_cursor:
                            for row in search_cursor:
                                currentPath = row[0]


                        L.Wrap('Rotate 90 Degrees selected...')
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
                        L.Wrap('Updating fields in PhotoPoints feature class...')
                        with arcpy.da.UpdateCursor(fcPhotoPoints, ['Orientation', 'PhotoPath'], where_clause=where) as cursor:
                            for row in cursor:
                                if row[0] == 'Landscape':
                                    newOrientation = 'Portrait'
                                else:
                                    newOrientation = 'Landscape'
                                row[0] = newOrientation
                                row[1] = newPath
                                cursor.updateRow(row)
                        L.Wrap('Field update complete.')
                        fovUpdater.Main(CurrentPhoto=True)
                        # Refresh Map Series to Reflect Changes
                        if ms.enabled:
                            # Force the UI to reset the Map Series
                            ms.enabled = False
                            ms.enabled = True # This effectively "reboots" the Map Series in the Catalog
                            ms.refresh()
                        return

# Execute the main function
if __name__ == '__main__':
    Main()
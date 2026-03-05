import math
import arcpy
import importlib

# Import Custom Libraries
import JLog
importlib.reload(JLog)
import fovUpdater
importlib.reload(fovUpdater)


def calculate_initial_compass_bearing(pointA, pointB):
    # jeromer, compassbearing.py, https://gist.github.com/jeromer/2005586#file-compassbearing-py
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")
    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])
    diffLong = math.radians(pointB[1] - pointA[1])
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))
    initial_bearing = math.atan2(x, y)
    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing


def marker2location(CurrentPhoto=True):
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

                # Get Marker Point Layer
                for lyr in mf.map.listLayers():
                    if "Marker Point" in lyr.name:
                        # Define Feature Class
                        fcMarkerPoint = lyr.dataSource

                        # Define Fields for Search Cursor & Later Update Cursor
                        fields = ['SHAPE@X', 'SHAPE@Y']
                        
                        # Create search Cursor and gather all selected rows in a list
                        L.Wrap('Reading Marker Point Coordinates...')
                        with arcpy.da.SearchCursor(fcMarkerPoint, fields) as search_cursor:
                            for row in search_cursor:
                                mpLon = row[0]
                                mpLat = row[1]

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

                                # Update FieldName field using the FieldValue value
                                L.Wrap(f"Setting Photo Location to {mpLat}, {mpLon}...")
                                with arcpy.da.UpdateCursor(fcPhotoPoints, fields, where_clause=where) as update_cursor:
                                    for row in update_cursor:
                                        row[0] = mpLon
                                        row[1] = mpLat
                                        update_cursor.updateRow(row)

                                # Rebuild Field of View Polygon for new location
                                fovUpdater.Main(CurrentPhoto=True)

                                # Re-Center Map Frame on new Photo Location point
                                sr_wgs_1984 = arcpy.SpatialReference(4326) 
                                point = arcpy.Point(mpLon, mpLat)
                                pt_geom = arcpy.PointGeometry(point, sr_wgs_1984)
                                mf.panToExtent(pt_geom.extent)


                                # Refresh Map Series (Shouldn't be needed, but Map Frame freezes otherwise)
                                if ms.enabled:
                                    # Force the UI to reset the Map Series
                                    ms.enabled = False
                                    ms.enabled = True # This effectively "reboots" the Map Series in the Catalog
                                    ms.refresh()

    else:
        arcpy.AddMessage("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
        arcpy.AddError("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")




def marker2heading(CurrentPhoto=True):
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

                # Get Marker Point Layer
                for lyr in mf.map.listLayers():
                    if "Marker Point" in lyr.name:
                        # Define Feature Class
                        fcMarkerPoint = lyr.dataSource

                        # Define Fields for Search Cursor & Later Update Cursor
                        fields = ['SHAPE@X', 'SHAPE@Y']
                        
                        # Create search Cursor and get Marker Point coordinates
                        L.Wrap('Reading Marker Point Coordinates...')
                        with arcpy.da.SearchCursor(fcMarkerPoint, fields) as search_cursor:
                            for row in search_cursor:
                                mpX = row[0]
                                mpY = row[1]

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

                                # Get current Photo Location coordinates
                                with arcpy.da.SearchCursor(fcPhotoPoints, fields, where_clause=where) as search_cursor:
                                    for row in search_cursor:
                                        photoX = row[0]
                                        photoY = row[1]

                                # Get Compass Bearing from Photo Location to Marker Point
                                pointA = (photoY, photoX)
                                pointB = (mpY, mpX)
                                compass_bearing = calculate_initial_compass_bearing(pointA, pointB)

                                # Write Compass Bearing as the Heading for the current Photo
                                fields = ['Heading']
                                with arcpy.da.UpdateCursor(fcPhotoPoints, fields, where_clause=where) as update_cursor:
                                    for row in update_cursor:
                                        row[0] = compass_bearing
                                        update_cursor.updateRow(row)

                                # Rebuild Field of View Polygon for new location
                                fovUpdater.Main(CurrentPhoto=True)

                                # Refresh Map Series (Shouldn't be needed, but Map Frame freezes otherwise)
                                if ms.enabled:
                                    # Force the UI to reset the Map Series
                                    ms.enabled = False
                                    ms.enabled = True # This effectively "reboots" the Map Series in the Catalog
                                    ms.refresh()

    else:
        arcpy.AddMessage("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
        arcpy.AddError("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")



def marker2distance(CurrentPhoto=True):
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

                # Get Marker Point Layer
                for lyr in mf.map.listLayers():
                    if "Marker Point" in lyr.name:
                        # Define Feature Class
                        fcMarkerPoint = lyr.dataSource

                        # Define Fields for Search Cursor & Later Update Cursor
                        fields = ['SHAPE@']
                        
                        # Create search Cursor and get Marker Point Shape object
                        with arcpy.da.SearchCursor(fcMarkerPoint, fields) as search_cursor:
                            for row in search_cursor:
                                mpShape = row[0]

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
                                with arcpy.da.SearchCursor(fcPhotoPoints, fields, where_clause=where) as search_cursor:
                                    for row in search_cursor:
                                        photoShape = row[0]

                                # Use ArcGIS Pro built-in function to calculate distance
                                distance = photoShape.angleAndDistanceTo(mpShape)[1]

                                # Write Distance as the MetersOfView value for the current Photo
                                fields = ['MetersOfView']
                                with arcpy.da.UpdateCursor(fcPhotoPoints, fields, where_clause=where) as update_cursor:
                                    for row in update_cursor:
                                        row[0] = distance
                                        update_cursor.updateRow(row)

                                # Rebuild Field of View Polygon for new location
                                fovUpdater.Main(CurrentPhoto=True)

                                # Refresh Map Series (Shouldn't be needed, but Map Frame freezes otherwise)
                                if ms.enabled:
                                    # Force the UI to reset the Map Series
                                    ms.enabled = False
                                    ms.enabled = True # This effectively "reboots" the Map Series in the Catalog
                                    ms.refresh()

    else:
        arcpy.AddMessage("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
        arcpy.AddError("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
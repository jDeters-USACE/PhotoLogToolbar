import os
import arcpy
import importlib

# Import Custom Libraries
import JLog
importlib.reload(JLog)
import fovUpdater
importlib.reload(fovUpdater)

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
                                mpLat = row[0]
                                mpLon = row[1]

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
                                        row[0] = mpLat
                                        row[1] = mpLon
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
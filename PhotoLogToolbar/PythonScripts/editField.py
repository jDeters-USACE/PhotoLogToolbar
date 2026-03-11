import arcpy
import importlib

# Import Custom Libraries
import JLog
importlib.reload(JLog)
import fovUpdater
importlib.reload(fovUpdater)
import backupFunctions
importlib.reload(backupFunctions)

def Main(FieldName, FieldValue):
    # Backup if Heading is changed
    if FieldName == "Heading":
        backupFunctions.create_photopoints_backup()
    # Set CurrentPhoto to True
    CurrentPhoto = True
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

                        # Update FieldName field using the FieldValue value
                        arcpy.AddMessage(f"Setting {FieldName} to {FieldValue}...")
                        with arcpy.da.UpdateCursor(fcPhotoPoints, [FieldName], where_clause=where) as cursor:
                            for row in cursor:
                                row[0] = FieldValue
                                cursor.updateRow(row)

                        # Update FOV if necessary
                        if FieldName == "Heading" or "MetersOfView" or "Orientation":
                            fovUpdater.Main(CurrentPhoto=True)

                        # Change Map Scale if necessary
                        if FieldName == "ViewHeight":
                            mf.camera.scale = FieldValue

        
        # Clear potential locks
        if 'cursor' in locals(): del cursor
        if 'row' in locals(): del row

        # Refresh Map Series to Reflect Changes
        if ms.enabled:
            # Force the UI to reset the Map Series
#            ms.enabled = False
#            ms.enabled = True # This effectively "reboots" the Map Series in the Catalog
            ms.refresh()

    else:
        arcpy.AddMessage("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
        arcpy.AddError("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
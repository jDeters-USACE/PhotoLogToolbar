import os
import arcpy

def Main(PhotoFolder=None, ProjectName=None, USACE_ID=None, Photographer=None, CurrentPhoto=False):
    # Reference the project currently open in ArcGIS Pro
    aprx = arcpy.mp.ArcGISProject("CURRENT")

    # Get the active view
    active_view = aprx.activeView

    # Reliable way to check if the active view is a layout
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
                        fc = lyr.dataSource

                        # Determine Where Clause
                        if CurrentPhoto:
                            # Get the current page's OID - ms.pageRow provides the attribute row of the current page index
                            current_oid = ms.pageRow.OBJECTID 
                            # Get the OID field name
                            oid_field = arcpy.Describe(fc).OIDFieldName
                            # reate a Where Clause to target ONLY this row
                            where = f"{oid_field} = {current_oid}"
                        else:
                            where = None

                        # Update Photo Folder Field
                        if str(PhotoFolder) != "None":
                            arcpy.AddMessage("PhotoFolder")
                            with arcpy.da.UpdateCursor(fc,['PhotoPath'], where_clause=where) as cursor:
                                for row in cursor:
                                    FileName = os.path.split(row[0])[1]
                                    row[0] = PhotoFolder + "\\" + FileName
                                    cursor.updateRow(row)

                        #Update Project Name Field
                        if str(ProjectName) != "None":
                            arcpy.AddMessage("ProjectName")
                            with arcpy.da.UpdateCursor(fc,['Project_Name'], where_clause=where) as cursor:
                                for row in cursor:
                                    row[0] = ProjectName
                                    cursor.updateRow(row)

                        # Update USACE_ID Field
                        if str(USACE_ID) != "None":
                            arcpy.AddMessage("USACE_ID")
                            with arcpy.da.UpdateCursor(fc,['USACE_ID'], where_clause=where) as cursor:
                                for row in cursor:
                                    row[0] = USACE_ID
                                    cursor.updateRow(row)

                        # Update Photographer Field
                        if str(Photographer) != "None":
                            arcpy.AddMessage("Photographer")
                            with arcpy.da.UpdateCursor(fc,['Photographer'], where_clause=where) as cursor:
                                for row in cursor:
                                    row[0] = Photographer
                                    cursor.updateRow(row)

#                        # Renumber Photos (In case of deletions)
#                        arcpy.AddMessage("Numbering")
#                        num = 1
#                        with arcpy.da.UpdateCursor(fc,['Number']) as cursor:
#                            for row in cursor:
#                                row[0] = num
#                                cursor.updateRow(row)
#                                num += 1
        
        # Clear potential locks
        if 'cursor' in locals(): del cursor
        if 'row' in locals(): del row

        # Refresh Map Series to Reflect Changes
        if ms.enabled:
            # Force the UI to reset the Map Series
            ms.enabled = False
            ms.enabled = True # This effectively "reboots" the Map Series in the Catalog
            ms.refresh()

    else:
        arcpy.AddMessage("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
        arcpy.AddError("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")

def EditField(FieldName, FieldValue):
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
                        fc = lyr.dataSource

                        # Determine Where Clause
                        if CurrentPhoto:
                            # Get the current page's OID - ms.pageRow provides the attribute row of the current page index
                            current_oid = ms.pageRow.OBJECTID 
                            # Get the OID field name
                            oid_field = arcpy.Describe(fc).OIDFieldName
                            # reate a Where Clause to target ONLY this row
                            where = f"{oid_field} = {current_oid}"
                        else:
                            where = None

                        # Update FieldName field using the FieldValue value
                        arcpy.AddMessage(f"Setting {FieldName} to {FieldValue}...")
                        with arcpy.da.UpdateCursor(fc,[FieldName], where_clause=where) as cursor:
                            for row in cursor:
                                row[0] = FieldValue
                                cursor.updateRow(row)
        
        # Clear potential locks
        if 'cursor' in locals(): del cursor
        if 'row' in locals(): del row

        # Refresh Map Series to Reflect Changes
        if ms.enabled:
            # Force the UI to reset the Map Series
            ms.enabled = False
            ms.enabled = True # This effectively "reboots" the Map Series in the Catalog
            ms.refresh()

    else:
        arcpy.AddMessage("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
        arcpy.AddError("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
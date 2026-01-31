import arcpy


def Main(PhotoFolder=None, ProjectName=None, USACE_ID=None, Photographer=None):
    # Reference the project currently open in ArcGIS Pro
    aprx = arcpy.mp.ArcGISProject("CURRENT")

    # Get the active view
    active_view = aprx.activeView

    # Reliable way to check if the active view is a layout
    if active_view is not None and hasattr(active_view, "pageHeight"):
        active_layout = active_view

        # Get Main Map Frame
        for mf in active_layout.listElements("MAPFRAME_ELEMENT"):
            if "Photo Log - Main" in mf.map.name:

                # Get Photo Location Layer
                for lyr in mf.map.listLayers():
                    if "Photo Location" in lyr.name:
                        fc = lyr.dataSource

                        # Update Photo Folder Field
                        if str(PhotoFolder) != "None":
                            arcpy.AddMessage("PhotoFolder")
                            with arcpy.da.UpdateCursor(fc,['PhotoPath']) as cursor:
                                for row in cursor:
                                    FileName = os.path.split(row[0])[1]
                                    row[0] = PhotoFolder + "\\" + FileName
                                    cursor.updateRow(row)

                        #Update Project Name Field
                        if str(ProjectName) != "None":
                            arcpy.AddMessage("ProjectName")
                            with arcpy.da.UpdateCursor(fc,['Project_Name']) as cursor:
                                for row in cursor:
                                    row[0] = ProjectName
                                    cursor.updateRow(row)

                        # Update USACE_ID Field
                        if str(USACE_ID) != "None":
                            arcpy.AddMessage("USACE_ID")
                            with arcpy.da.UpdateCursor(fc,['USACE_ID']) as cursor:
                                for row in cursor:
                                    row[0] = USACE_ID
                                    cursor.updateRow(row)

                        # Update Photographer Field
                        if str(Photographer) != "None":
                            arcpy.AddMessage("Photographer")
                            with arcpy.da.UpdateCursor(fc,['Photographer']) as cursor:
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

                # Refresh Map Series to Reflect Changes
                ms = active_layout.mapSeries
                ms.refresh()

    else:
        arcpy.AddMessage("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")
        arcpy.AddError("The current active view is not a layout. Move to a Mapped Photo Log Layout and re-run tool.")


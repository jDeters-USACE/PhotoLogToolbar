# -*- coding: utf-8 -*-
import arcpy
import os
from datetime import datetime
import importlib

import JLog
importlib.reload(JLog)
import fovUpdater
importlib.reload(fovUpdater)

def create_photopoints_backup():
    """
    Creates a dated backup of the 'PhotoPoints' feature class without adding it to the map.
    It locates the feature class through the active layout in the current ArcGIS Pro project.
    """
    # Store the original environment setting to restore it later
    original_add_to_map_setting = arcpy.env.addOutputsToMap
    
    # Create Instance of JLog
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=3)

    try:
        # Reference the project currently open in ArcGIS Pro
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        L.Wrap("Successfully accessed the current ArcGIS Pro project.")

        # Get the active view (must be a layout)
        active_view = aprx.activeView
        if not (active_view and hasattr(active_view, "pageHeight")):
            arcpy.AddError("The current view is not a layout. Please switch to a Mapped Photo Log layout and re-run.")
            L.Wrap("Error: The current view is not a layout.")
            return

        active_layout = active_view
        L.Wrap(f"Active layout found: {active_layout.name}")

        # Find the main map frame and the PhotoPoints layer
        fc_photopoints = None
        for mf in active_layout.listElements("MAPFRAME_ELEMENT"):
            if "Photo Log - Main" in mf.map.name:
                for lyr in mf.map.listLayers():
                    if "Photo Location" in lyr.name:
                        fc_photopoints = lyr.dataSource
                        break
                if fc_photopoints:
                    break
        
        if not fc_photopoints:
            arcpy.AddError("Could not find 'Photo Location' layer in a 'Photo Log - Main' map frame.")
            L.Wrap("Error: Could not find the required layer or map frame.")
            return

        L.Wrap(f"Found PhotoPoints feature class: {fc_photopoints}")

        # Build a name for the backup file using a GDB-compliant date format
        gdb_path = os.path.dirname(fc_photopoints)
        project_folder = os.path.dirname(gdb_path)
        log_file_path = os.path.join(project_folder, "backups.log")
        now_str = datetime.now().strftime('%Y_%m_%d_%H_%M_%S') 
        backup_name = f"PhotoPoints_backup_{now_str}"
        backup_path = os.path.join(gdb_path, backup_name)
        
        L.Wrap(f"Backup path generated: {backup_path}")

        # Check if that feature already exists
        if arcpy.Exists(backup_path):
            message = f"Backup for today ('{backup_name}') already exists. No action taken."
            L.Wrap(message)
            L.Wrap(message)
            return
        
        # Temporarily disable adding outputs to the map
        arcpy.env.addOutputsToMap = False
        L.Wrap("Temporarily disabled adding outputs to the map.")

        # If it does not exist, it copies the current PhotoPoints feature class
        L.Wrap(f"'{backup_name}' does not exist. Proceeding with copy operation...")
        arcpy.management.CopyFeatures(
            in_features=fc_photopoints,
            out_feature_class=backup_path
        )
        
        # Write the successful backup name to the log file
        with open(log_file_path, 'a') as log_file:
            log_file.write(backup_name + '\n')

        success_message = f"Successfully created backup: {backup_name}"
        L.Wrap(success_message)

    except arcpy.ExecuteError:
        error_message = arcpy.GetMessages(2)
        arcpy.AddError(f"ArcPy Execution Error: {error_message}")
        L.Wrap(f"ArcPy Execution Error: {error_message}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {str(e)}")
        L.Wrap(f"An unexpected error occurred: {str(e)}")
    finally:
        # Always restore the original environment setting
        arcpy.env.addOutputsToMap = original_add_to_map_setting
        L.Wrap(f"Restored 'addOutputsToMap' setting to: {original_add_to_map_setting}")



#def restore_from_backup(backup_name):
#    """
#    Restores the 'PhotoPoints' feature class from a specified backup by overwriting it.
#    This function will now raise any exceptions, allowing the C# caller to display the full traceback.
#    """
#    # Create Instance of JLog
#    L = JLog.PrintLog(Log="C:\\\\Temp\\\\PhotoLogToolbar_LOG.txt", Indent=3)
#
#    # Reference the project currently open in ArcGIS Pro
#    aprx = arcpy.mp.ArcGISProject("CURRENT")
#    
#    # Get the active view (must be a layout)
#    active_view = aprx.activeView
#    if not (active_view and hasattr(active_view, "pageHeight")):
#        # Raise a specific error that arcpy can report
#        arcpy.AddError("The current view is not a layout. Please switch to a Mapped Photo Log layout.")
#        # Exit gracefully if not in a layout view
#        return
#
#    # Find the active GDB path from the 'Photo Location' layer
#    fc_photopoints = None
#    for mf in active_view.listElements("MAPFRAME_ELEMENT"):
#        if "Photo Log - Main" in mf.map.name:
#            for lyr in mf.map.listLayers():
#                if "Photo Location" in lyr.name:
#                    fc_photopoints = lyr.dataSource
#                    break
#            if fc_photopoints:
#                break
#    
#    if not fc_photopoints:
#        arcpy.AddError("Could not find 'Photo Location' layer in a 'Photo Log - Main' map frame.")
#        return
#
#    gdb_path = os.path.dirname(fc_photopoints)
#    backup_fc_path = os.path.join(gdb_path, backup_name)
#    destination_path = os.path.join(gdb_path, "PhotoPoints")
#
#    if not arcpy.Exists(backup_fc_path):
#        arcpy.AddError(f"Backup '{backup_name}' not found in the geodatabase: {backup_fc_path}")
#        return
#
#    L.Wrap(f"Starting restore from '{backup_name}'...")
#    
#    # Set the crucial environment setting to allow the overwrite
#    arcpy.env.overwriteOutput = True
#    
#    # Perform the single, atomic Copy operation. Any failure here will now
#    # raise a detailed exception that will be caught by the C# code.
#    arcpy.management.Copy(
#        in_data=backup_fc_path,
#        out_data=destination_path
#    )
#    
#    L.Wrap("Restore complete. Refreshing map series...")
#    # Refresh the map series to reflect the restored data
#    active_view.mapSeries.refresh()

def restore_from_backup(backup_name):
    """
    Restores the 'PhotoPoints' feature class by overwriting its contents,
    without removing the layer from the map.
    """
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=3)
    
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    active_view = aprx.activeView
    if not (active_view and hasattr(active_view, "pageHeight")):
        arcpy.AddError("The current view is not a layout.")
        return

    fc_photopoints = None
    for mf in active_view.listElements("MAPFRAME_ELEMENT"):
        if "Photo Log - Main" in mf.map.name:
            for lyr in mf.map.listLayers("Photo Location"):
                fc_photopoints = lyr.dataSource
                break
        if fc_photopoints:
            break
    
    if not fc_photopoints:
        arcpy.AddError("Could not find 'Photo Location' layer.")
        return

    gdb_path = os.path.dirname(fc_photopoints)
    backup_fc_path = os.path.join(gdb_path, backup_name)
    
    if not arcpy.Exists(backup_fc_path):
        arcpy.AddError(f"Backup '{backup_name}' not found.")
        return

    L.Wrap(f"Starting restore from '{backup_name}'...")

    
    # 1. Delete all features from the current PhotoPoints feature class.
    #    This empties the table but keeps the feature class and its schema intact.
    arcpy.management.DeleteFeatures(fc_photopoints)
    L.Wrap("Cleared existing features from PhotoPoints.")

    # 2. Append the features from the backup into the now-empty PhotoPoints feature class.
    #    'NO_TEST' means we assume the schemas match, which they should.
    arcpy.management.Append(
        inputs=backup_fc_path,
        target=fc_photopoints,
        schema_type="NO_TEST"
    )
    L.Wrap("Appended features from backup.")

    fovUpdater.Main()

    L.Wrap("Restore complete. Refreshing map series...")
    active_view.mapSeries.refresh()



if __name__ == '__main__':
    create_photopoints_backup()

# -*- coding: utf-8 -*-
import arcpy
import os
from datetime import datetime
import importlib

import JLog
importlib.reload(JLog)

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
        today_str = datetime.now().strftime('%Y_%m_%d') 
        backup_name = f"PhotoPoints_backup_{today_str}"
        backup_path = os.path.join(gdb_path, backup_name)
        
        L.Wrap(f"Backup path generated: {backup_path}")

        # Check if that feature already exists
        if arcpy.Exists(backup_path):
            message = f"Backup for today ('{backup_name}') already exists. No action taken."
            L.Wrap(message)
            L.Wrap(message)
            return
        
        # --- START OF MODIFICATION ---
        # Temporarily disable adding outputs to the map
        arcpy.env.addOutputsToMap = False
        L.Wrap("Temporarily disabled adding outputs to the map.")
        # --- END OF MODIFICATION ---

        # If it does not exist, it copies the current PhotoPoints feature class
        L.Wrap(f"'{backup_name}' does not exist. Proceeding with copy operation...")
        arcpy.management.CopyFeatures(
            in_features=fc_photopoints,
            out_feature_class=backup_path
        )
        
        success_message = f"Successfully created backup: {backup_name}"
        L.Wrap(success_message)
        L.Wrap(success_message)

    except arcpy.ExecuteError:
        error_message = arcpy.GetMessages(2)
        arcpy.AddError(f"ArcPy Execution Error: {error_message}")
        L.Wrap(f"ArcPy Execution Error: {error_message}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {str(e)}")
        L.Wrap(f"An unexpected error occurred: {str(e)}")
    finally:
        # --- START OF MODIFICATION ---
        # Always restore the original environment setting
        arcpy.env.addOutputsToMap = original_add_to_map_setting
        L.Wrap(f"Restored 'addOutputsToMap' setting to: {original_add_to_map_setting}")
        # --- END OF MODIFICATION ---

if __name__ == '__main__':
    create_photopoints_backup()

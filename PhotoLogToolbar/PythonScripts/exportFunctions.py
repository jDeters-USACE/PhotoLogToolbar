import arcpy
import os
import JLog

def export_and_open_photo_log(OpenPDF=True):
    """
    This script performs the following actions on the current ArcGIS Pro project:
    1. Unchecks the 'Marker Point' layer.
    2. Ensures the export directory '{Default Project Folder}\\Export\\Photo Logs' exists.
    3. Exports all pages of the Map Series to a single, optimized-size PDF.
    4. Opens the newly generated PDF file.
    5. Re-enables the 'Marker Point' layer after export.
    6. Saves the project.
    """
    L = JLog.PrintLog(Log="C:\\\\Temp\\\\PhotoLogToolbar_LOG.txt", Indent=3)
    
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    photo_log_layout = None
    for lyt in reversed(aprx.listLayouts()):
        if "Mapped Photo Log" in lyt.name:
            photo_log_layout = lyt
            break
    
    if not photo_log_layout:
        L.Wrap("Error: No layout with 'Mapped Photo Log' in its name was found.")
        return

    L.Wrap(f"Processing layout: {photo_log_layout.name}")
    layers_to_toggle = []
    
    try:
        # --- Action 1: Turn the layer OFF ---
        L.Wrap("\nStep 1: Disabling 'Marker Point' layer for export...")
        for mf in photo_log_layout.listElements("MAPFRAME_ELEMENT"):
            for lyr in mf.map.listLayers():
                if lyr.name == "Marker Point":
                    if lyr.visible:
                        lyr.visible = False
                        layers_to_toggle.append(lyr)
                        L.Wrap(f"- Layer '{lyr.name}' in map '{mf.map.name}' has been turned OFF.")
        
        # --- Action 2: Ensure export folder exists ---
        L.Wrap("\nStep 2: Verifying export directory...")
        project_folder = os.path.dirname(aprx.filePath)
        export_folder = os.path.join(project_folder, "Export", "Photo Logs")
        os.makedirs(export_folder, exist_ok=True)
        L.Wrap(f"- Export directory is ready: {export_folder}")
        
        # --- Action 3: Export to PDF (with optimizations) ---
        L.Wrap("\nStep 3: Exporting layout to optimized PDF...")
        map_series = photo_log_layout.mapSeries
        if not map_series or not map_series.enabled:
            L.Wrap("Error: The selected layout does not have an enabled Map Series.")
            return

        base_pdf_name = f"{photo_log_layout.name}.pdf"
        output_pdf_path = os.path.join(export_folder, base_pdf_name)
        
        counter = 1
        while os.path.exists(output_pdf_path):
            name_part, extension_part = os.path.splitext(base_pdf_name)
            new_name = f"{name_part} ({counter}){extension_part}"
            output_pdf_path = os.path.join(export_folder, new_name)
            counter += 1

        # --- MODIFICATION START: Corrected image_quality to a valid preset ---
        map_series.exportToPDF(
            output_pdf_path, 
            "ALL",
            image_compression = "ADAPTIVE",
            image_quality = 3,               # Use 'BETTER' (1=BEST, 2=BETTER, 3=NORMAL, 4=WORSE, 5=WORST)
            compress_vector_graphics = True,
            resolution = 240
        )
        # --- MODIFICATION END ---

        L.Wrap(f"- Successfully exported to: {output_pdf_path}")
        
        # --- Action 4: Open the PDF in a new process ---
        if OpenPDF and os.path.exists(output_pdf_path):
            L.Wrap("\nStep 4: Opening exported PDF...")
            os.startfile(output_pdf_path)
            L.Wrap("- The PDF has been opened in your default viewer.")
            
    except Exception as e:
        L.Wrap(f"An error occurred during the process: {e}")
        L.Wrap("--- Detailed ArcPy Error Messages ---")
        L.Wrap(arcpy.GetMessages(2))
        L.Wrap("-----------------------------------")
        
    finally:
        # --- Action 5: Turn the layer back ON ---
        L.Wrap("\nStep 5: Re-enabling 'Marker Point' layer...")
        if layers_to_toggle:
            for lyr in layers_to_toggle:
                lyr.visible = True
                L.Wrap(f"- Layer '{lyr.name}' has been turned back ON.")
        # --- Action 6: Save the project ---
        aprx.save()
        L.Wrap("\nStep 6: Project saved.")
        L.Wrap("\nProcess Complete.")

# Execute the main function
if __name__ == '__main__':
    export_and_open_photo_log()

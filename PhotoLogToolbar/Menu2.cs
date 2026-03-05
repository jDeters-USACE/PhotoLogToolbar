using ArcGIS.Core.CIM;
using ArcGIS.Core.Data;
using ArcGIS.Core.Geometry;
using ArcGIS.Desktop.Catalog;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Core.Geoprocessing;
using ArcGIS.Desktop.Editing;
using ArcGIS.Desktop.Extensions;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Dialogs;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.KnowledgeGraph;
using ArcGIS.Desktop.Layouts;
using ArcGIS.Desktop.Mapping;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using static System.Runtime.InteropServices.JavaScript.JSType;
using System.Windows;
using System.Windows.Media;

// Use an alias to stop the "Ambiguous Reference" error (resolve ambiguity between ArcGIS Pro and WPF MessageBoxes)
using ProMsg = ArcGIS.Desktop.Framework.Dialogs.MessageBox;

namespace PhotoLogToolbar
{
    internal class Menu2_button1 : Button
    {
        protected override async void OnClick()
        {
            // Setup paths
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string pythonScriptsDir = Path.Combine(assemblyDir, "PythonScripts");
            string toolBoxPath = Path.Combine(pythonScriptsDir, "PhotologToolbar.pyt");

            // Use the backslash specifically to separate the .pyt from the Tool Class Name
            string toolName = $@"{toolBoxPath}\marker2location";

            // Verify the file actually exists before trying to open it
            if (!File.Exists(toolBoxPath))
            {
                ProMsg.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }

            // Set arguments
            var args = Geoprocessing.MakeValueArray("true");

            // Run the geoprocessing tool on the QueuedTask thread; use an async lambda so awaiting inside is valid.
            await QueuedTask.Run(async () =>
            {
                var result = await Geoprocessing.ExecuteToolAsync(toolName, args);
                // Optionally inspect result here or handle messages.
            });
        }
    }

    internal class Menu2_button2 : Button
    {
        protected override async void OnClick()
        {
            // Setup paths
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string pythonScriptsDir = Path.Combine(assemblyDir, "PythonScripts");
            string toolBoxPath = Path.Combine(pythonScriptsDir, "PhotologToolbar.pyt");

            // Use the backslash specifically to separate the .pyt from the Tool Class Name
            string toolName = $@"{toolBoxPath}\marker2heading";

            // Verify the file actually exists before trying to open it
            if (!File.Exists(toolBoxPath))
            {
                ProMsg.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }

            // Set arguments
            var args = Geoprocessing.MakeValueArray("true");

            // Run the geoprocessing tool on the QueuedTask thread; use an async lambda so awaiting inside is valid.
            await QueuedTask.Run(async () =>
            {
                var result = await Geoprocessing.ExecuteToolAsync(toolName, args);
                // Optionally inspect result here or handle messages.
            });
        }
    }

    internal class Menu2_button3 : Button
    {
        protected override async void OnClick()
        {
            // Setup paths
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string pythonScriptsDir = Path.Combine(assemblyDir, "PythonScripts");
            string toolBoxPath = Path.Combine(pythonScriptsDir, "PhotologToolbar.pyt");

            // Use the backslash specifically to separate the .pyt from the Tool Class Name
            string toolName = $@"{toolBoxPath}\marker2distance";

            // Verify the file actually exists before trying to open it
            if (!File.Exists(toolBoxPath))
            {
                ProMsg.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }

            // Set arguments
            var args = Geoprocessing.MakeValueArray("true");

            // Run the geoprocessing tool on the QueuedTask thread; use an async lambda so awaiting inside is valid.
            await QueuedTask.Run(async () =>
            {
                var result = await Geoprocessing.ExecuteToolAsync(toolName, args);
                // Optionally inspect result here or handle messages.
            });
        }
    }

    internal class Menu2_button4 : Button
    {
        protected override void OnClick()
        {
            var layoutView = LayoutView.Active;
            if (layoutView == null) return;

            QueuedTask.Run(async () =>
            {
                try
                {
                    var mapFrame = layoutView.Layout.GetElementsAsFlattenedList()
                                    .OfType<MapFrame>()
                                    .FirstOrDefault(mf => mf.Name == "Main Map Frame");

                    if (mapFrame == null) return;

                    // Locate the Marker Point Layer
                    var markerLayer = mapFrame.Map.GetLayersAsFlattenedList()
                                      .OfType<FeatureLayer>()
                                      .FirstOrDefault(l => l.Name == "Marker Point");

                    if (markerLayer == null)
                    {
                        ProMsg.Show("Layer 'Marker Point' not found in the map frame.");
                        return;
                    }

                    // ENSURE LAYER IS ENABLED
                    // Turn the layer visibility ON if it is unchecked
                    if (!markerLayer.IsVisible)
                    {
                        markerLayer.SetVisibility(true);
                    }

                    // Ensure the layer is Selectable (optional, but helpful for editing)
                    if (!markerLayer.IsSelectable)
                    {
                        markerLayer.SetSelectable(true);
                    }

                    // Create a new Edit Operation
                    var editOp = new EditOperation() { Name = "Update Photo Log Marker" };

                    // Clear existing markers (if any) before adding the new one
                    using (var selection = markerLayer.Select(new QueryFilter()))
                    {
                        var oids = selection.GetObjectIDs();
                        if (oids.Count > 0) editOp.Delete(markerLayer, oids);
                    }

                    // Execute and then SaveEdits
                    if (editOp.Execute())
                    {
                        await ArcGIS.Desktop.Core.Project.Current.SaveEditsAsync();
                    }

                    // Unselect the MarkerPoint Tool by selecting the Explore Tool
                    await FrameworkApplication.SetCurrentToolAsync("esri_mapping_exploreTool");
                }
                catch (System.Exception ex)
                {
                    ProMsg.Show($"Error: {ex.Message}");
                }
            });
        }

    }
}

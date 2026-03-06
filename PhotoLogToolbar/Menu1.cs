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

namespace PhotoLogToolbar
{
    internal class Menu1_button1 : Button
    {
        protected override async void OnClick()
        {
            // Setup paths
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string pythonScriptsDir = Path.Combine(assemblyDir, "PythonScripts");
            string toolBoxPath = Path.Combine(pythonScriptsDir, "PhotologToolbar.pyt");

            // Use the backslash specifically to separate the .pyt from the Tool Class Name
            string toolName = $@"{toolBoxPath}\CreateNewPhotoLog";

            // Verify the file actually exists before trying to open it
            if (!File.Exists(toolBoxPath))
            {
                MessageBox.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }

            // Activate the Geoprocessing Pane (Must be on UI thread)
            // This ensures the pane exists and is visible before the tool tries to open in it
            var gpPane = FrameworkApplication.DockPaneManager.Find("esri_geoprocessing_toolBoxes");
            gpPane?.Activate();

            await QueuedTask.Run(() =>
            {
                // Add true to force the GP pane to activate/show
                Geoprocessing.OpenToolDialog(toolName, null, null, true);
            });
        }
    }

    internal class Menu1_button2 : Button
    {
        protected override async void OnClick()
        {
            // Setup paths
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string pythonScriptsDir = Path.Combine(assemblyDir, "PythonScripts");
            string toolBoxPath = Path.Combine(pythonScriptsDir, "PhotologToolbar.pyt");

            // Use the backslash specifically to separate the .pyt from the Tool Class Name
            string toolName = $@"{toolBoxPath}\EditExistingPhotoLogParameters";

            // Verify the file actually exists before trying to open it
            if (!File.Exists(toolBoxPath))
            {
                MessageBox.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }

            // Activate the Geoprocessing Pane (Must be on UI thread)
            // This ensures the pane exists and is visible before the tool tries to open in it
            var gpPane = FrameworkApplication.DockPaneManager.Find("esri_geoprocessing_toolBoxes");
            gpPane?.Activate();

            await QueuedTask.Run(() =>
            {
                // Add true to force the GP pane to activate/show
                Geoprocessing.OpenToolDialog(toolName, null, null, true);
            });
        }
    }

    internal class Menu1_button3 : Button
    {
        protected override async void OnClick()
        {
            // Setup paths
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string pythonScriptsDir = Path.Combine(assemblyDir, "PythonScripts");
            string toolBoxPath = Path.Combine(pythonScriptsDir, "PhotologToolbar.pyt");

            // Use the backslash specifically to separate the .pyt from the Tool Class Name
            string toolName = $@"{toolBoxPath}\exportPhotoLog";

            // Verify the file actually exists before trying to open it
            if (!File.Exists(toolBoxPath))
            {
                MessageBox.Show($"Toolbox not found at: {toolBoxPath}");
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


}

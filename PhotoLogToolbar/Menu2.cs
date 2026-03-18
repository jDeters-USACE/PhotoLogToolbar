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
using System.Threading;
using System.Threading.Tasks;
using static System.Runtime.InteropServices.JavaScript.JSType;
using System.Windows;
using System.Windows.Media;
using Microsoft.VisualBasic;

// Use an alias to stop the "Ambiguous Reference" error
using ProMsg = ArcGIS.Desktop.Framework.Dialogs.MessageBox;

namespace PhotoLogToolbar
{

    internal class Menu2_button1 : Button
    {
        protected override async void OnClick()
        {
            if (string.IsNullOrWhiteSpace(PhotoLogSessionManager.SessionAuthorName))
            {
                string author = Interaction.InputBox("Please enter your name to attribute changes for this session.", "Attribute Session Author", "");
                if (string.IsNullOrWhiteSpace(author)) { return; }
                PhotoLogSessionManager.SessionAuthorName = author;
            }

            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string pythonScriptsDir = Path.Combine(assemblyDir, "PythonScripts");
            string toolBoxPath = Path.Combine(pythonScriptsDir, "PhotologToolbar.pyt");

            // Use a single backslash separator.
            string toolName = $"{toolBoxPath}\\marker2location";

            if (!File.Exists(toolBoxPath))
            {
                ProMsg.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }
            var args = Geoprocessing.MakeValueArray("true", PhotoLogSessionManager.SessionAuthorName);

            await QueuedTask.Run(async () =>
            {
                var result = await Geoprocessing.ExecuteToolAsync(toolName, args, null, CancellationToken.None, null, GPExecuteToolFlags.AddToHistory);
                if (result.IsFailed)
                {
                    var sb = new StringBuilder();
                    sb.AppendLine($"Geoprocessing tool failed: {toolName}");
                    foreach (var message in result.Messages)
                    {
                        sb.AppendLine($"{message.Type}: {message.Text}");
                    }
                    ProMsg.Show(sb.ToString(), "----------------------------------Geoprocessing Error----------------------------------");
                }
            });
        }
    }

    internal class Menu2_button2 : Button
    {
        protected override async void OnClick()
        {
            if (string.IsNullOrWhiteSpace(PhotoLogSessionManager.SessionAuthorName))
            {
                string author = Interaction.InputBox("Please enter your name to attribute changes for this session.", "Attribute Session Author", "");
                if (string.IsNullOrWhiteSpace(author)) { return; }
                PhotoLogSessionManager.SessionAuthorName = author;
            }

            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string pythonScriptsDir = Path.Combine(assemblyDir, "PythonScripts");
            string toolBoxPath = Path.Combine(pythonScriptsDir, "PhotologToolbar.pyt");

            // Use a single backslash separator.
            string toolName = $"{toolBoxPath}\\marker2heading";

            if (!File.Exists(toolBoxPath))
            {
                ProMsg.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }
            var args = Geoprocessing.MakeValueArray("true", PhotoLogSessionManager.SessionAuthorName);

            await QueuedTask.Run(async () =>
            {
                var result = await Geoprocessing.ExecuteToolAsync(toolName, args, null, CancellationToken.None, null, GPExecuteToolFlags.AddToHistory);
                if (result.IsFailed)
                {
                    var sb = new StringBuilder();
                    sb.AppendLine($"Geoprocessing tool failed: {toolName}");
                    foreach (var message in result.Messages)
                    {
                        sb.AppendLine($"{message.Type}: {message.Text}");
                    }
                    ProMsg.Show(sb.ToString(), "----------------------------------Geoprocessing Error----------------------------------");
                }
            });
        }
    }

    internal class Menu2_button3 : Button
    {
        protected override async void OnClick()
        {
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string pythonScriptsDir = Path.Combine(assemblyDir, "PythonScripts");
            string toolBoxPath = Path.Combine(pythonScriptsDir, "PhotologToolbar.pyt");

            // Use a single backslash separator.
            string toolName = $"{toolBoxPath}\\marker2distance";

            if (!File.Exists(toolBoxPath))
            {
                ProMsg.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }
            var args = Geoprocessing.MakeValueArray("true");

            await QueuedTask.Run(async () =>
            {
                var result = await Geoprocessing.ExecuteToolAsync(toolName, args, null, CancellationToken.None, null, GPExecuteToolFlags.AddToHistory);
                if (result.IsFailed)
                {
                    var sb = new StringBuilder();
                    sb.AppendLine($"Geoprocessing tool failed: {toolName}");
                    foreach (var message in result.Messages)
                    {
                        sb.AppendLine($"{message.Type}: {message.Text}");
                    }
                    ProMsg.Show(sb.ToString(), "----------------------------------Geoprocessing Error----------------------------------");
                }
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

                    var markerLayer = mapFrame.Map.GetLayersAsFlattenedList()
                                      .OfType<FeatureLayer>()
                                      .FirstOrDefault(l => l.Name == "Marker Point");
                    if (markerLayer == null)
                    {
                        ProMsg.Show("Layer 'Marker Point' not found in the map frame.");
                        return;
                    }

                    if (!markerLayer.IsVisible)
                    {
                        markerLayer.SetVisibility(true);
                    }

                    if (!markerLayer.IsSelectable)
                    {
                        markerLayer.SetSelectable(true);
                    }

                    var editOp = new EditOperation() { Name = "Update Photo Log Marker" };

                    using (var selection = markerLayer.Select(new QueryFilter()))
                    {
                        var oids = selection.GetObjectIDs();
                        if (oids.Count > 0) editOp.Delete(markerLayer, oids);
                    }

                    if (editOp.Execute())
                    {
                        await ArcGIS.Desktop.Core.Project.Current.SaveEditsAsync();
                    }

                    await FrameworkApplication.SetCurrentToolAsync("esri_mapping_exploreTool");
                }
                catch (System.Exception ex)
                {
                    var sb = new StringBuilder();
                    sb.AppendLine("An exception occurred during the edit operation:");
                    sb.AppendLine(ex.Message);
                    sb.AppendLine(ex.StackTrace);
                    ProMsg.Show(sb.ToString(), "----------------------------------Edit Operation Error----------------------------------");
                }
            });
        }
    }
}

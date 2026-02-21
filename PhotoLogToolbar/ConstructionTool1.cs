using ArcGIS.Core.CIM;
using ArcGIS.Core.Data;
using ArcGIS.Core.Geometry;
using ArcGIS.Desktop.Catalog;
using ArcGIS.Desktop.Core;
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
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Media;

// Use an alias to stop the "Ambiguous Reference" error (resolve ambiguity between ArcGIS Pro and WPF MessageBoxes)
using ProMsg = ArcGIS.Desktop.Framework.Dialogs.MessageBox;


namespace PhotoLogToolbar
{
    internal class ConstructionTool1 : MapTool
    {
        public ConstructionTool1()
        {
            IsSketchTool = false;
            UsesCurrentTemplate = false;
            Cursor = System.Windows.Input.Cursors.Cross;
        }

        protected override void OnToolMouseDown(MapViewMouseButtonEventArgs e)
        {
            var layoutView = LayoutView.Active;
            if (layoutView == null) return;

            e.Handled = true;

            // Capture the Client Point (Pixels) from the mouse event
            var clientPoint = e.ClientPoint;

            QueuedTask.Run(async () =>
            {
                try
                {
                    // Transform Client Pixels directly to Page Units (e.g., Inches)
                    //   -This avoids the DPI scaling drift seen with ScreenToPage
                    var pagePoint = layoutView.ClientToPage(clientPoint);

                    var mapFrame = layoutView.Layout.GetElementsAsFlattenedList()
                                    .OfType<MapFrame>()
                                    .FirstOrDefault(mf => mf.Name == "Main Map Frame");

                    if (mapFrame == null) return;

                    // Translate Layout Page Units to Map Coordinates
                    var mapCoord = mapFrame.PageToMap(pagePoint);
                    if (mapCoord == null) return;

                    // Create MapPoint using the Map's Spatial Reference for precision
                    var mapPoint = MapPointBuilderEx.CreateMapPoint(mapCoord, mapFrame.Map.SpatialReference);

                    // DEBUG - Verification of Output Coordinates
                    // ProMsg.Show($"Calculated X: {mapPoint.X:F10}\nCalculated Y: {mapPoint.Y:F10}");


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

                    // Create a new feature at the clicked location and capture the result
                    //  -Use the overload: Create(layer, geometry, attributes, callback)
                    //  -We pass null for attributes to satisfy the method signature
                    //long newOid = -1;
                    //editOp.Create(markerLayer, mapPoint, null, oid => newOid = oid);
                    editOp.Create(markerLayer, mapPoint);

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

        protected override void OnToolMouseMove(MapViewMouseEventArgs e)
        {
            Cursor = System.Windows.Input.Cursors.Cross;
            base.OnToolMouseMove(e);
        }
    }
}


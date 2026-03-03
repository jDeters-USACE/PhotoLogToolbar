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
using ArcGIS.Desktop.Mapping.Events;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Reflection;
using System.IO;
using System.Text;
using System.Threading.Tasks;

#nullable enable

namespace PhotoLogToolbar
{
    /// <summary>
    /// ComboBox1
    ///
    /// Now subscribes to MapLayoutWatcher to detect layout/view changes:
    ///  - when layout becomes incompatible (not a LayoutView) all combo boxes can be disabled by the watcher;
    ///  - when layout changes, items are repopulated (one-time) if a Photo Location layer exists;
    ///  - if Photo Location is missing in the "Main Map Frame", the control is disabled and shows "N/A".
    /// </summary>
    internal class ComboBox1 : ComboBox
    {
        private bool _isInitialized;

        public ComboBox1()
        {
            // Populate items (fire-and-forget).
            _ = PopulateItemsAsync();

            // Subscribe to layout changes and map-series changes.
            MapLayoutWatcher.Instance.Subscribe(OnLayoutChanged);
            MapSeriesWatcher.Instance.Subscribe(OnMapSeriesPageChanged);
        }

        ~ComboBox1()
        {
            try
            {
                MapLayoutWatcher.Instance.Unsubscribe(OnLayoutChanged);
                MapSeriesWatcher.Instance.Unsubscribe(OnMapSeriesPageChanged);
            }
            catch { }
        }

        protected override void OnDropDownOpened()
        {
            // no-op: avoid modifying items while open
        }

        private static string EscapeForSql(string value) => value?.Replace("'", "''") ?? string.Empty;
        private static string QuoteFieldForFileGdb(string fieldName) => $"\"{fieldName}\"";

        private async Task<string?> GetCurrentMapSeriesIndexValueAsync()
        {
            return await QueuedTask.Run(() =>
            {
                var layoutView = LayoutView.Active;
                if (layoutView == null) return null;

                var layout = layoutView.Layout;
                if (layout == null) return null;

                var mapFrame = layout.GetElements().OfType<MapFrame>().FirstOrDefault();
                if (mapFrame == null) return null;

                var mapSeries = layout.MapSeries;
                if (mapSeries == null) return null;

                if (!string.IsNullOrEmpty(mapSeries.CurrentPageNumber))
                    return mapSeries.CurrentPageNumber;

                try
                {
                    var indexLayer = mapFrame?.Map?.GetLayersAsFlattenedList()
                        .OfType<FeatureLayer>()
                        .FirstOrDefault(fl => fl.Name.Equals("Photo Location"));
                    if (indexLayer == null) return null;

                    var cimMapSeries = mapSeries.GetDefinition();
                    var pageFieldName = cimMapSeries?.CurrentPageID.ToString();
                    if (string.IsNullOrEmpty(mapSeries.CurrentPageNumber) || string.IsNullOrEmpty(pageFieldName))
                        return null;

                    var qf = new QueryFilter
                    {
                        WhereClause = $"OBJECTID = {mapSeries.CurrentPageNumber}",
                        SubFields = pageFieldName
                    };
                    using var cursor = indexLayer.Search(qf);
                    if (cursor.MoveNext())
                    {
                        using var row = cursor.Current;
                        return row[pageFieldName]?.ToString();
                    }
                }
                catch { return null; }

                return null;
            });
        }

        // Populate items once (or again when layout changes to a different compatible layout).
        private async Task PopulateItemsAsync()
        {
            // If already populated, skip. (MapLayoutWatcher will clear IsInitialized when layout changes.)
            if (_isInitialized) return;

            var mv = MapView.Active;
            var map = mv?.Map;
            var featureLayer = map?.GetLayersAsFlattenedList().OfType<FeatureLayer>()
                .FirstOrDefault(fl => fl.Name.Equals("Photo Location"));

            // If feature layer is missing -> show N/A and disable
            if (featureLayer == null)
            {
                // clear any existing items and show "N/A"
                Clear();
                Add(new ComboBoxItem("N/A", null, "Photo Location layer not found in Main Map Frame"));
                SelectedItem = ItemCollection.FirstOrDefault();
                Enabled = false;
                _isInitialized = true;
                return;
            }

            // Otherwise populate items (QueuedTask for feature access).
            await QueuedTask.Run(() =>
            {
                // read all features and add items
                using var featCursor = featureLayer.Search(new QueryFilter { WhereClause = null, SubFields = "*" });
                while (featCursor.MoveNext())
                {
                    using var feature = featCursor.Current as Feature;
                    if (feature == null) continue;

                    var numberValue = feature["Number"]?.ToString();
                    var displayText = numberValue ?? "<no number>";
                    var item = new FeatureComboBoxItem(displayText, feature.GetShape().Clone(), numberValue);

                    Add(item);
                }
            });

            _isInitialized = true;
            Enabled = true;

            // After populating, set selection to current MapSeries page if present
            _ = UpdateSelectionToMapSeriesAsync();
        }

        // Update only the SelectedItem to match current MapSeries page.
        private async Task UpdateSelectionToMapSeriesAsync()
        {
            if (!_isInitialized) return;

            var currentPageValue = await GetCurrentMapSeriesIndexValueAsync();

            // Find match on UI thread
            var match = ItemCollection.FirstOrDefault(i => i is FeatureComboBoxItem f && f.PageKey == currentPageValue);
            SelectedItem = match ?? ItemCollection.FirstOrDefault();
        }

        // Layout change handler invoked by MapLayoutWatcher.
        private void OnLayoutChanged(object? sender, MapLayoutWatcher.LayoutChangedEventArgs e)
        {
            // If the active view is not a LayoutView, disable and show N/A across subscribers.
            if (!e.IsLayoutView)
            {
                // Clear and show N/A disabled
                Clear();
                Add(new ComboBoxItem("N/A", null, "Active view is not a compatible layout view"));
                SelectedItem = ItemCollection.FirstOrDefault();
                Enabled = false;
                _isInitialized = true;
                return;
            }

            // If layout changed and there is no photo location, show N/A and disable.
            if (!e.HasPhotoLocation)
            {
                Clear();
                Add(new ComboBoxItem("N/A", null, "Photo Location layer not found in Main Map Frame"));
                SelectedItem = ItemCollection.FirstOrDefault();
                Enabled = false;
                _isInitialized = true;
                return;
            }

            // Otherwise a compatible layout with Photo Location exists: clear state so PopulateItemsAsync repopulates.
            _isInitialized = false;
            Clear();
            Enabled = true;

            // Repopulate items for the new layout (one-time).
            _ = PopulateItemsAsync();
        }

        // MapSeries page change handler: update selected item only.
        private void OnMapSeriesPageChanged(object? sender, string? newPageNumber)
        {
            _ = UpdateSelectionToMapSeriesAsync();
        }

        // When user selects an item, set the MapSeries current page.
        protected override void OnSelectionChange(ComboBoxItem item)
        {
            if (!Enabled) return; // ignore selection when disabled

            if (item is FeatureComboBoxItem featComboBoxItem)
            {
                var selectedPageKey = featComboBoxItem.PageKey;
                if (!string.IsNullOrEmpty(selectedPageKey))
                {
                    _ = QueuedTask.Run(() =>
                    {
                        try
                        {
                            var layoutView = LayoutView.Active;
                            var layout = layoutView?.Layout;
                            var mapSeries = layout?.MapSeries;
                            if (mapSeries != null)
                                mapSeries.SetCurrentPageNumber(selectedPageKey);
                        }
                        catch { }
                    });
                }
            }
        }
    }
}
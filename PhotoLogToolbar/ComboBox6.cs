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
using ArcGIS.Desktop.Mapping.Events;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Timers;

namespace PhotoLogToolbar
{
    /// <summary>
    /// Represents the ComboBox
    /// </summary>
    internal class ComboBox6 : ComboBox
    {
        private bool _isInitialized;
        private MapSeries? _subscribedMapSeries;

        // Polling timer to detect MapSeries page changes (ArcGIS Pro SDK 3.4 has no PropertyChanged on MapSeries)
        private Timer? _mapSeriesPollTimer;
        private string? _lastPageNumber;

        public ComboBox6()
        {
            // Fire-and-forget initialization; do not block the ctor.
            _ = UpdateComboAsync();

            // Ensure we are subscribed to map series changes (via polling fallback)
            SubscribeToMapSeriesEvents();
        }

        protected override void OnDropDownOpened()
        {
            // refresh subscription in case the active layout / map frame changed
            SubscribeToMapSeriesEvents();

            _ = UpdateComboAsync();
        }

        private static string EscapeForSql(string value) => value?.Replace("'", "''") ?? string.Empty;
        private static string QuoteFieldForFileGdb(string fieldName) => $"\"{fieldName}\"";

#nullable enable
        private async Task<string?> GetCurrentMapSeriesIndexValueAsync()
#nullable restore
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

                if (!string.IsNullOrEmpty(mapSeries.CurrentPageName))
                    return mapSeries.CurrentPageName;

                if (!string.IsNullOrEmpty(mapSeries.CurrentPageName))
                    return mapSeries.CurrentPageName;

                // As a last resort, try to read the index layer using CurrentPageIndex and its index field
                try
                {
                    var indexLayer = mapFrame?.Map?.GetLayersAsFlattenedList().OfType<FeatureLayer>().FirstOrDefault(fl => fl.Name.Equals("Photo Location"));
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
                catch
                {
                    return null;
                }

                return null;
            });
        }

        private async Task UpdateComboAsync()
        {
            if (_isInitialized)
            {
                Clear();
                SelectedItem = ItemCollection.FirstOrDefault();
            }

            _isInitialized = false;

            var mv = MapView.Active;
            var map = mv?.Map;
            var featureLayer = map?.GetLayersAsFlattenedList().OfType<FeatureLayer>().FirstOrDefault(fl => fl.Name.Equals("Photo Location"));
            if (featureLayer == null)
            {
                Enabled = true;
                return;
            }

            // Resolve the map series page value (numeric per your message)
            var currentPageValue = await GetCurrentMapSeriesIndexValueAsync();

            await QueuedTask.Run(() =>
            {
                // Determine if the target field is numeric
                bool isNumericField = false;
                try
                {
                    using var fc = featureLayer.GetFeatureClass();
                    var def = fc.GetDefinition();
                    var fld = def.GetFields().FirstOrDefault(f => f.Name.Equals("Number", StringComparison.OrdinalIgnoreCase));
                    if (fld != null)
                    {
                        isNumericField = fld.FieldType == FieldType.Integer
                                      || fld.FieldType == FieldType.SmallInteger
                                      || fld.FieldType == FieldType.Single
                                      || fld.FieldType == FieldType.Double;
                    }
                }
                catch
                {
                    // If we can't determine type, default to string-safe behavior (quote)
                    isNumericField = false;
                }

#nullable enable
                string? pageWhereClause = null;
#nullable restore
                if (!string.IsNullOrEmpty(currentPageValue))
                {
                    var fieldName = QuoteFieldForFileGdb("Number");
                    var escaped = EscapeForSql(currentPageValue);
                    pageWhereClause = isNumericField ? $"{fieldName} = {escaped}" : $"{fieldName} = '{escaped}'";
                }

                var layerDefQuery = featureLayer.DefinitionQuery;
#nullable enable
                string? combinedWhere = null;
#nullable restore
                if (!string.IsNullOrWhiteSpace(layerDefQuery) && !string.IsNullOrWhiteSpace(pageWhereClause))
                    combinedWhere = $"({layerDefQuery}) AND ({pageWhereClause})";
                else if (!string.IsNullOrWhiteSpace(layerDefQuery))
                    combinedWhere = layerDefQuery;
                else if (!string.IsNullOrWhiteSpace(pageWhereClause))
                    combinedWhere = pageWhereClause;

                if (string.IsNullOrWhiteSpace(combinedWhere))
                {
                    using var featCursor = featureLayer.Search();
                    while (featCursor.MoveNext())
                    {
                        using var feature = featCursor.Current as Feature;
                        Add(new FeatureComboBoxItem(feature["Comment"]?.ToString(), feature.GetShape().Clone()));
                        SelectedItem = ItemCollection.FirstOrDefault();
                    }
                }
                else
                {
                    var qf = new QueryFilter { WhereClause = combinedWhere, SubFields = "*" };
                    using var featCursor = featureLayer.Search(qf);
                    while (featCursor.MoveNext())
                    {
                        using var feature = featCursor.Current as Feature;
                        Add(new FeatureComboBoxItem(feature["Comment"]?.ToString(), feature.GetShape().Clone()));
                        SelectedItem = ItemCollection.FirstOrDefault();
                    }
                }
            });

            _isInitialized = true;
            Enabled = true;
        }

        private void SubscribeToMapSeriesEvents()
        {
            // run on QueuedTask because Layout/MapSeries are thread-affine
            _ = QueuedTask.Run(() =>
            {
                var layoutView = LayoutView.Active;
                var layout = layoutView?.Layout;
                var mapSeries = layout?.MapSeries;

                // nothing to do
                if (_subscribedMapSeries == mapSeries) return;

                // stop and dispose previous timer if any
                _mapSeriesPollTimer?.Stop();
                _mapSeriesPollTimer?.Dispose();
                _mapSeriesPollTimer = null;
                _lastPageNumber = null;

                _subscribedMapSeries = mapSeries;

                if (_subscribedMapSeries != null)
                {
                    // capture initial page number
                    _lastPageNumber = _subscribedMapSeries.CurrentPageNumber;

                    // Create polling timer (safe fallback for ArcGIS Pro SDK 3.4)
                    // Timer runs on threadpool; inside Elapsed we safely call QueuedTask to access MapSeries
                    _mapSeriesPollTimer = new Timer(1000);
                    _mapSeriesPollTimer.AutoReset = true;
                    _mapSeriesPollTimer.Elapsed += async (s, e) =>
                    {
                        try
                        {
                            var current = await QueuedTask.Run(() =>
                            {
                                var lv = LayoutView.Active;
                                return lv?.Layout?.MapSeries?.CurrentPageNumber;
                            });

                            if (current != _lastPageNumber)
                            {
                                _lastPageNumber = current;
                                _ = UpdateComboAsync();
                            }
                        }
                        catch
                        {
                            // swallow - polling should continue
                        }
                    };
                    _mapSeriesPollTimer.Start();
                }
            });
        }

        private void MapSeries_PropertyChanged(object? sender, PropertyChangedEventArgs e)
        {
            // react to page index/name changes
            if (e.PropertyName == nameof(MapSeries.CurrentPageNumber) || e.PropertyName == nameof(MapSeries.CurrentPageName))
            {
                // page changed — refresh the combo
                _ = UpdateComboAsync();
            }
        }

        protected override void OnSelectionChange(ComboBoxItem item)
        {
            if (item is FeatureComboBoxItem featComboBoxItem)
            {
                MapView.Active?.ZoomToAsync(featComboBoxItem.Geometry, TimeSpan.FromSeconds(1.5));
            }
        }
    }
}
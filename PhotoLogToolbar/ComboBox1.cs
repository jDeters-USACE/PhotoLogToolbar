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


namespace PhotoLogToolbar
{
    /// <summary>
    /// Represents the ComboBox
    /// </summary>
    internal class ComboBox1 : ComboBox
    {
        private bool _isInitialized;

        public ComboBox1()
        {
            // Fire-and-forget initialization; do not block the ctor.
            _ = UpdateComboAsync();
        }

        protected override void OnDropDownOpened()
        {
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
                        Add(new FeatureComboBoxItem(feature["Number"]?.ToString(), feature.GetShape().Clone()));
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
                        Add(new FeatureComboBoxItem(feature["Number"]?.ToString(), feature.GetShape().Clone()));
                        SelectedItem = ItemCollection.FirstOrDefault();
                    }
                }
            });

            _isInitialized = true;
            Enabled = true;
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
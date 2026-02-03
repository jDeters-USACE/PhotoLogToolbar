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

#nullable enable

namespace PhotoLogToolbar
{
    /// <summary>
    /// ComboBox2
    ///
    /// This control represents one of the ComboBox controls that populate themselves
    /// from features in the "Photo Location" feature layer. It uses the centralized
    /// MapSeriesWatcher to detect when MapSeries.CurrentPageNumber changes and refreshes
    /// its contents in response.
    ///
    /// CONCEPTUAL OVERVIEW FOR NOVICES:
    ///   - The ArcGIS Pro SDK uses thread-affine objects (Layout, MapSeries, MapFrame, etc.).
    ///     These objects must be read/modified on the QueuedTask thread. That is why methods
    ///     that access ArcGIS objects call QueuedTask.Run.
    ///   - UI work and control lifetime are managed by WPF and the ArcGIS Pro framework. The
    ///     ComboBox class we inherit from provides lifecycle entry points such as constructors
    ///     and OnDropDownOpened. We use those to initialize and refresh the control.
    ///   - Instead of creating a timer inside each ComboBox, we subscribe to a single global
    ///     MapSeriesWatcher. This reduces resource use and centralizes the logic to detect
    ///     page changes.
    /// </summary>
    internal class ComboBox2 : ComboBox
    {
        #region Fields - persistent control state
        // Track whether the ComboBox has been initialized previously. Used to clear and re-select.
        private bool _isInitialized;

        // NOTE: we previously had per-control timers. Those are removed in favor of MapSeriesWatcher.
        #endregion

        #region Constructor / lifecycle
        // Constructor: start initial population and subscribe to the centralized watcher.
        public ComboBox2()
        {
            // Start the first population asynchronously (fire-and-forget); do not block constructor.
            // UpdateComboAsync accesses ArcGIS objects using QueuedTask internally.
            _ = UpdateComboAsync();

            // Subscribe to the central MapSeries watcher. When the watcher detects a page change
            // it will invoke OnMapSeriesPageChanged which refreshes this combo.
            MapSeriesWatcher.Instance.Subscribe(OnMapSeriesPageChanged);
        }

        // Finalizer (destructor): ensure we unsubscribe from the centralized watcher to avoid
        // keeping references alive longer than necessary. If your controls live for the app lifetime
        // this is optional, but it's shown here for completeness and to demonstrate cleanup patterns.
        ~ComboBox2()
        {
            try
            {
                MapSeriesWatcher.Instance.Unsubscribe(OnMapSeriesPageChanged);
            }
            catch
            {
                // Swallow in finalizer; do not throw from a destructor.
            }
        }
        #endregion

        #region UI hooks
        // Called by the ComboBox framework when the dropdown opens. We refresh subscription (no-op)
        // and enqueue a refresh to ensure the list is current when the user opens it.
        protected override void OnDropDownOpened()
        {
            // Refresh contents because the active layout or map frame may have changed since construction.
            _ = UpdateComboAsync();
        }
        #endregion

        #region Helper utilities (small helpers used in queries)
        // Escape a string for use inside SQL WHERE clause string literals.
        // NOTE: with the assumption that MapSeries page value is numeric we still use this helper
        // in a paranoid fashion when constructing WHERE clauses.
        private static string EscapeForSql(string value) => value?.Replace("'", "''") ?? string.Empty;

        // Quote a field name using double quotes (suitable for file geodatabase / ArcGIS queries).
        private static string QuoteFieldForFileGdb(string fieldName) => $"\"{fieldName}\"";
        #endregion

        #region MapSeries index value resolution
        /*
         * GetCurrentMapSeriesIndexValueAsync
         *
         * Purpose:
         *   Attempt to obtain the current MapSeries index value. Under the user's assumption
         *   this will always be numeric and is available through MapSeries.CurrentPageNumber.
         *
         * Steps (high level):
         *   1. Use QueuedTask.Run to safely access LayoutView.Active and Layout.MapSeries.
         *   2. If CurrentPageNumber is available, return it immediately (string).
         *   3. As a fallback, attempt to query the index layer to resolve the index field value.
         *
         * Threading:
         *   - This method itself runs asynchronously but the body that touches ArcGIS objects
         *     executes on the QueuedTask thread.
         */
        private async Task<string?> GetCurrentMapSeriesIndexValueAsync()
        {
            return await QueuedTask.Run(() =>
            {
                // Acquire the active layout view (if any). If none, we cannot proceed.
                var layoutView = LayoutView.Active;
                if (layoutView == null) return null;

                // Layout is the page composition; if absent we cannot proceed.
                var layout = layoutView.Layout;
                if (layout == null) return null;

                // MapFrame is the element that contains the Map shown on the layout page.
                var mapFrame = layout.GetElements().OfType<MapFrame>().FirstOrDefault();
                if (mapFrame == null) return null;

                // MapSeries contains paging information for the layout. If no map series, return.
                var mapSeries = layout.MapSeries;
                if (mapSeries == null) return null;

                // Primary expected route: numeric page number is available via CurrentPageNumber.
                if (!string.IsNullOrEmpty(mapSeries.CurrentPageNumber))
                    return mapSeries.CurrentPageNumber;

                // Fallback: inspect the index layer to resolve the index field using the CIM definition.
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

                    // Query the index layer by OBJECTID equal to the current page number (numeric).
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
                    // If anything fails while reading the index layer, return null so callers can fall back.
                    return null;
                }

                return null;
            });
        }
        #endregion

        #region Core refresh logic - populates the ComboBox items
        /*
         * UpdateComboAsync
         *
         * Purpose:
         *   Populate the ComboBox with items from the "Photo Location" feature layer,
         *   optionally filtered by the MapSeries current page number.
         *
         * Key behaviors:
         *   - Clears previous items when running subsequent refreshes.
         *   - Always executes ArcGIS data access on a QueuedTask thread.
         *   - Under the numeric-page assumption we construct numeric WHERE clauses (no quotes).
         */
        private async Task UpdateComboAsync()
        {
            // If control was initialized before, clear contents so we repopulate from scratch.
            if (_isInitialized)
            {
                Clear();
                SelectedItem = ItemCollection.FirstOrDefault();
            }

            _isInitialized = false;

            // Get the active map from the MapView (this is safe on the calling thread).
            var mv = MapView.Active;
            var map = mv?.Map;

            // Find the feature layer named "Photo Location". We use GetLayersAsFlattenedList to search all sublayers.
            var featureLayer = map?.GetLayersAsFlattenedList().OfType<FeatureLayer>().FirstOrDefault(fl => fl.Name.Equals("Photo Location"));
            if (featureLayer == null)
            {
                // If the layer is not present, Populate "N/A", Disable the control, and exit gracefully.
                Clear();
                Add(new ComboBoxItem("N/A", null, "Photo Location layer not found in Main Map Frame"));
                SelectedItem = ItemCollection.FirstOrDefault();
                Enabled = false;
                _isInitialized = true;
                return;
            }

            // Resolve the map series page value (expected numeric).
            var currentPageValue = await GetCurrentMapSeriesIndexValueAsync();

            // Perform the feature read on the QueuedTask thread because feature access is thread-affine.
            await QueuedTask.Run(() =>
            {
                // Build the numeric page WHERE clause if we obtained a page value.
                string? pageWhereClause = null;
                if (!string.IsNullOrEmpty(currentPageValue))
                {
                    var fieldName = QuoteFieldForFileGdb("Number");
                    var escaped = EscapeForSql(currentPageValue); // still escape to be defensive
                    pageWhereClause = $"{fieldName} = {escaped}";
                }

                // Combine any layer definition query with our page filter (if present).
                var layerDefQuery = featureLayer.DefinitionQuery;
                string? combinedWhere = null;
                if (!string.IsNullOrWhiteSpace(layerDefQuery) && !string.IsNullOrWhiteSpace(pageWhereClause))
                    combinedWhere = $"({layerDefQuery}) AND ({pageWhereClause})";
                else if (!string.IsNullOrWhiteSpace(layerDefQuery))
                    combinedWhere = layerDefQuery;
                else if (!string.IsNullOrWhiteSpace(pageWhereClause))
                    combinedWhere = pageWhereClause;

                // Execute the appropriate search: unfiltered or filtered.
                if (string.IsNullOrWhiteSpace(combinedWhere))
                {
                    using var featCursor = featureLayer.Search();
                    while (featCursor.MoveNext())
                    {
                        using var feature = featCursor.Current as Feature;
                        Add(new ComboBoxItem(feature["Orientation"]?.ToString()));
                    }
                }
                else
                {
                    var qf = new QueryFilter { WhereClause = combinedWhere, SubFields = "*" };
                    using var featCursor = featureLayer.Search(qf);
                    while (featCursor.MoveNext())
                    {
                        using var feature = featCursor.Current as Feature;
                        Add(new ComboBoxItem(feature["Orientation"]?.ToString()));
                    }
                }

                // Select the first item by default. You may refine selection logic to match currentPageValue.
                SelectedItem = ItemCollection.FirstOrDefault();
            });

            // Mark as initialized and enable the control.
            _isInitialized = true;
            Enabled = true;
        }
        #endregion

        #region MapSeries change handler (invoked by MapSeriesWatcher)
        // This handler is invoked by the centralized MapSeriesWatcher whenever the page number changes.
        // We respond by refreshing this control's contents. The handler does not itself access ArcGIS
        // objects; it simply enqueues UpdateComboAsync which uses QueuedTask internally.
        private void OnMapSeriesPageChanged(object? sender, string? newPageNumber)
        {
            // Fire-and-forget refresh; do not block the watcher or UI thread.
            _ = UpdateComboAsync();
        }
        #endregion

        #region Selection handling
        // When the user selects an item in the combo, zoom to that feature geometry in the active MapView.
        // We call MapView.Active?.ZoomToAsync which is safe to call from the UI thread.
        protected override void OnSelectionChange(ComboBoxItem item)
        {
            //if (item is FeatureComboBoxItem featComboBoxItem)
            //{
            //    // Smooth zoom to the feature's geometry over 1.5 seconds.
            //    MapView.Active?.ZoomToAsync(featComboBoxItem.Geometry, TimeSpan.FromSeconds(1.5));
            //}
        }
        #endregion
    }
}
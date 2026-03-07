using ArcGIS.Core.Data;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Dialogs;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Layouts;
using ArcGIS.Desktop.Mapping;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

#nullable enable

// NOTE: This implementation assumes a custom class 'FeatureComboBoxItem' exists, like so:
public class FeatureComboBoxItem : ComboBoxItem
{
    public string PageKey { get; }
    public FeatureComboBoxItem(string text, ArcGIS.Core.Geometry.Geometry geometry, string pageKey)
        : base(text, geometry)
    {
        PageKey = pageKey;
    }
}

namespace PhotoLogToolbar
{
    /// <summary>
    /// ComboBox1 - Refactored for stability to navigate the Map Series.
    /// </summary>
    internal class ComboBox1 : ComboBox
    {
        private bool _isUpdating = false;

        #region Constructor / lifecycle

        public ComboBox1()
        {
            _ = UpdateAsync();
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
            catch { /* Swallow */ }
        }

        #endregion

        #region UI hooks
        protected override void OnDropDownOpened() { }
        #endregion

        #region Core Refresh Logic
        /// <summary>
        /// A single, consolidated method to populate the item list and select the correct item.
        /// </summary>
        private async Task UpdateAsync()
        {
            if (_isUpdating) return;
            _isUpdating = true;

            try
            {
                var featureLayer = MapView.Active?.Map?.GetLayersAsFlattenedList()
                                       .OfType<FeatureLayer>()
                                       .FirstOrDefault(fl => fl.Name.Equals("Photo Location"));

                if (featureLayer == null)
                {
                    Clear();
                    Add(new ComboBoxItem("N/A", null, "Photo Location layer not found"));
                    SelectedItem = ItemCollection.FirstOrDefault();
                    Enabled = false;
                    return;
                }

                // If the list is empty, populate it. This happens on first run or after a layout change.
                // ✅ CORRECTED: Use this.ItemCollection.Count
                if (this.ItemCollection.Count == 0)
                {
                    await QueuedTask.Run(() =>
                    {
                        // ✅ CORRECTED: Pass a single string to SubFields, not a string array.
                        using var featCursor = featureLayer.Search(new QueryFilter { SubFields = "Number" });
                        while (featCursor.MoveNext())
                        {
                            using var feature = featCursor.Current;
                            var numberValue = feature["Number"]?.ToString();
                            if (string.IsNullOrEmpty(numberValue)) continue;

                            var item = new FeatureComboBoxItem(numberValue, null, numberValue);
                            Add(item);
                        }
                    });
                }

                // Now, ensure the correct item is selected based on the current map series page.
                var currentPageNumber = await QueuedTask.Run(() => LayoutView.Active?.Layout?.MapSeries?.CurrentPageNumber);

                var itemToSelect = ItemCollection.OfType<FeatureComboBoxItem>().FirstOrDefault(i => i.PageKey == currentPageNumber);
                this.SelectedItem = itemToSelect ?? ItemCollection.FirstOrDefault();

                Enabled = true;
            }
            finally
            {
                _isUpdating = false;
            }
        }
        #endregion

        #region Watcher Handlers
        private void OnLayoutChanged(object? sender, MapLayoutWatcher.LayoutChangedEventArgs e)
        {
            // A layout change means we need to fully repopulate the list.
            Clear();
            _ = UpdateAsync();
        }

        private void OnMapSeriesPageChanged(object? sender, string? newPageNumber)
        {
            _ = UpdateAsync();
        }
        #endregion

        #region Action Handling

        /// <summary>
        /// When user selects an item, set the MapSeries current page. This is the primary action.
        /// </summary>
        protected override void OnSelectionChange(ComboBoxItem item)
        {
            if (_isUpdating || !Enabled || item == null) return;

            if (item is FeatureComboBoxItem featComboBoxItem && !string.IsNullOrEmpty(featComboBoxItem.PageKey))
            {
                var selectedPageKey = featComboBoxItem.PageKey;

                var currentPageNumber = LayoutView.Active?.Layout?.MapSeries?.CurrentPageNumber;
                if (selectedPageKey == currentPageNumber) return;

                _ = QueuedTask.Run(() =>
                {
                    try
                    {
                        var mapSeries = LayoutView.Active?.Layout?.MapSeries;
                        mapSeries?.SetCurrentPageNumber(selectedPageKey);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show($"Failed to set map series page: {ex.Message}", "Error");
                    }
                });
            }
        }
        #endregion
    }
}

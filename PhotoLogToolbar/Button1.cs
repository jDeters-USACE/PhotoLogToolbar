using ArcGIS.Core.Data;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Layouts;
using ArcGIS.Desktop.Mapping;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

#nullable enable

namespace PhotoLogToolbar
{
    internal class Button1 : Button
    {
        public Button1()
        {
            _ = UpdateButtonStateAsync();
            MapSeriesWatcher.Instance.Subscribe(OnMapStateChanged);
            MapLayoutWatcher.Instance.Subscribe(OnLayoutStateChanged);
        }

        ~Button1()
        {
            try
            {
                MapSeriesWatcher.Instance.Unsubscribe(OnMapStateChanged);
                MapLayoutWatcher.Instance.Unsubscribe(OnLayoutStateChanged);
            }
            catch { /* Swallow */ }
        }

        private void OnMapStateChanged(object? sender, string? newPageNumber) => _ = UpdateButtonStateAsync();
        private void OnLayoutStateChanged(object? sender, MapLayoutWatcher.LayoutChangedEventArgs e) => _ = UpdateButtonStateAsync();

        protected override void OnClick()
        {
            _ = QueuedTask.Run(() =>
            {
                var mapSeries = LayoutView.Active?.Layout?.MapSeries;
                if (mapSeries == null) return;

                var pageKeys = GetOrderedPageKeys();
                if (pageKeys == null) return;

                var currentPage = mapSeries.CurrentPageNumber;
                var currentIndex = pageKeys.IndexOf(currentPage);

                if (currentIndex > 0)
                {
                    mapSeries.SetCurrentPageNumber(pageKeys[currentIndex - 1]);
                }
            });
        }

        private async Task UpdateButtonStateAsync()
        {
            this.Enabled = await QueuedTask.Run(() =>
            {
                var mapSeries = LayoutView.Active?.Layout?.MapSeries;
                if (mapSeries == null) return false;

                var pageKeys = GetOrderedPageKeys();
                if (pageKeys == null) return false;

                var currentIndex = pageKeys.IndexOf(mapSeries.CurrentPageNumber);
                return currentIndex > 0;
            });
        }

        /// <summary>
        /// This helper method correctly queries the index layer to get a sorted list of all page keys,
        /// using the exact same logic that ComboBox1 uses to populate itself.
        /// </summary>
        private List<string>? GetOrderedPageKeys()
        {
            // Based on ComboBox1, we find the "Photo Location" layer.
            var featureLayer = MapView.Active?.Map?.GetLayersAsFlattenedList()
                .OfType<FeatureLayer>()
                .FirstOrDefault(fl => fl.Name.Equals("Photo Location"));

            if (featureLayer == null) return null;

            // Based on ComboBox1, the page key is stored in the "Number" field.
            const string pageNumberField = "Number";
            var pageKeys = new List<string>();

            var qf = new QueryFilter
            {
                SubFields = pageNumberField,
                // The PostfixClause is the correct way to sort the query results.
                PostfixClause = $"ORDER BY {pageNumberField}"
            };

            using (var cursor = featureLayer.Search(qf))
            {
                while (cursor.MoveNext())
                {
                    var key = cursor.Current[pageNumberField]?.ToString();
                    if (!string.IsNullOrEmpty(key))
                        pageKeys.Add(key);
                }
            }
            return pageKeys;
        }
    }
}

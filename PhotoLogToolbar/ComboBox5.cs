using ArcGIS.Core.Data;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Core.Geoprocessing;
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
using System.Reflection;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

#nullable enable

namespace PhotoLogToolbar
{
    /// <summary>
    /// ComboBox5 - Refactored for stability and correct event handling.
    /// </summary>
    internal class ComboBox5 : ComboBox
    {
        private bool _isUpdating = false;

        #region Constructor / lifecycle

        public ComboBox5()
        {
            _ = UpdateComboAsync();
            MapSeriesWatcher.Instance.Subscribe(OnMapSeriesPageChanged);
            MapLayoutWatcher.Instance.Subscribe(OnLayoutChanged);
        }

        ~ComboBox5()
        {
            try
            {
                MapSeriesWatcher.Instance.Unsubscribe(OnMapSeriesPageChanged);
                MapLayoutWatcher.Instance.Unsubscribe(OnLayoutChanged);
            }
            catch { /* Swallow */ }
        }

        #endregion

        #region UI hooks and Helpers
        protected override void OnDropDownOpened() { }
        private static string EscapeForSql(string value) => value?.Replace("'", "''") ?? string.Empty;
        private static string QuoteFieldForFileGdb(string fieldName) => $"\"{fieldName}\"";
        #endregion

        #region MapSeries index value resolution
        private async Task<string?> GetCurrentMapSeriesIndexValueAsync()
        {
            return await QueuedTask.Run(() => LayoutView.Active?.Layout?.MapSeries?.CurrentPageNumber);
        }
        #endregion

        #region Core refresh logic
        private async Task UpdateComboAsync()
        {
            if (_isUpdating) return;
            _isUpdating = true;

            try
            {
                var previouslySelectedItem = this.SelectedItem as ComboBoxItem;
                Clear();

                var featureLayer = MapView.Active?.Map?.GetLayersAsFlattenedList()
                                       .OfType<FeatureLayer>()
                                       .FirstOrDefault(fl => fl.Name.Equals("Photo Location"));

                if (featureLayer == null)
                {
                    Add(new ComboBoxItem("N/A", null, "Photo Location layer not found"));
                    SelectedItem = ItemCollection.FirstOrDefault();
                    Enabled = false;
                    return;
                }

                var currentPageValue = await GetCurrentMapSeriesIndexValueAsync();
                string? currentFeatureValue = null;
                var allFeatureValues = new HashSet<string>();

                await QueuedTask.Run(() =>
                {
                    // Query all features to populate the dropdown list fully
                    using (var cursor = featureLayer.Search(new QueryFilter { SubFields = "MetersOfView" }))
                    {
                        while (cursor.MoveNext())
                        {
                            var val = cursor.Current["MetersOfView"]?.ToString();
                            if (!string.IsNullOrWhiteSpace(val))
                            {
                                allFeatureValues.Add(val);
                            }
                        }
                    }

                    // Separately, find the value for the *current* map series page
                    if (!string.IsNullOrEmpty(currentPageValue))
                    {
                        var qf = new QueryFilter { WhereClause = $"{QuoteFieldForFileGdb("Number")} = {EscapeForSql(currentPageValue)}", SubFields = "MetersOfView" };
                        using (var cursor = featureLayer.Search(qf))
                        {
                            if (cursor.MoveNext())
                            {
                                currentFeatureValue = cursor.Current["MetersOfView"]?.ToString();
                            }
                        }
                    }
                });

                // Populate the ComboBox with all unique values found
                foreach (var itemText in allFeatureValues.OrderBy(v => double.TryParse(v, out double n) ? n : double.MaxValue))
                {
                    Add(new ComboBoxItem(itemText));
                }

                // The correct pattern: Find the matching ComboBoxItem and set SelectedItem.
                var itemToSelect = ItemCollection.OfType<ComboBoxItem>().FirstOrDefault(i => i.Text == currentFeatureValue);
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
        private void OnMapSeriesPageChanged(object? sender, string? newPageNumber) => _ = UpdateComboAsync();
        private void OnLayoutChanged(object? sender, MapLayoutWatcher.LayoutChangedEventArgs e) => _ = UpdateComboAsync();
        #endregion

        #region Action Handling

        /// <summary>
        /// Fires when a user selects an item from the dropdown list.
        /// </summary>
        protected override async void OnSelectionChange(ComboBoxItem item)
        {
            if (_isUpdating || item == null || string.IsNullOrWhiteSpace(item.Text))
            {
                return;
            }
            await RunGeoprocessingTool(item.Text);
        }

        /// <summary>
        /// Fires when the user presses Enter after typing a value.
        /// </summary>
        protected override async void OnEnter()
        {
            if (_isUpdating || string.IsNullOrWhiteSpace(this.Text))
            {
                return;
            }
            await RunGeoprocessingTool(this.Text);
        }

        /// <summary>
        /// Runs the geoprocessing tool and triggers a UI refresh upon completion.
        /// </summary>
        private async Task RunGeoprocessingTool(string fieldValue)
        {
            string fieldName = "MetersOfView"; // The field this ComboBox controls
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string toolBoxPath = Path.Combine(assemblyDir, "PythonScripts", "PhotologToolbar.pyt");
            string toolName = $"{toolBoxPath}\\EditField"; // Correct tool path

            if (!File.Exists(toolBoxPath))
            {
                MessageBox.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }

            var args = Geoprocessing.MakeValueArray(fieldName, fieldValue);

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
                    MessageBox.Show(sb.ToString(), "Geoprocessing Error");
                }
            });

            // After the tool runs, refresh the UI to reflect any changes.
            await UpdateComboAsync();
        }
        #endregion
    }
}

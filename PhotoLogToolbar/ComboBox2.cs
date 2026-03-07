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
    /// ComboBox2 - Refactored to act as a command-launcher for photo rotation.
    /// </summary>
    internal class ComboBox2 : ComboBox
    {
        private bool _isUpdating = false;
        private const string RotateCommandText = "Rotate 90° Clockwise";

        #region Constructor / lifecycle

        public ComboBox2()
        {
            _ = UpdateComboAsync();
            MapSeriesWatcher.Instance.Subscribe(OnMapSeriesPageChanged);
            MapLayoutWatcher.Instance.Subscribe(OnLayoutChanged);
        }

        ~ComboBox2()
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

                await QueuedTask.Run(() =>
                {
                    if (!string.IsNullOrEmpty(currentPageValue))
                    {
                        var qf = new QueryFilter { WhereClause = $"{QuoteFieldForFileGdb("Number")} = {EscapeForSql(currentPageValue)}", SubFields = "Orientation" };
                        using (var cursor = featureLayer.Search(qf))
                        {
                            if (cursor.MoveNext())
                            {
                                currentFeatureValue = cursor.Current["Orientation"]?.ToString();
                            }
                        }
                    }
                });

                // Add the static "Rotate" command option.
                Add(new ComboBoxItem(RotateCommandText));

                // The correct pattern: Set SelectedItem to show the current orientation value.
                // Since this ComboBox should not have "Rotate..." as a valid data value, we will
                // create and select an item for the current feature's orientation value.
                if (!string.IsNullOrEmpty(currentFeatureValue))
                {
                    Add(new ComboBoxItem(currentFeatureValue));
                    this.SelectedItem = ItemCollection.OfType<ComboBoxItem>().FirstOrDefault(i => i.Text == currentFeatureValue);
                }
                else
                {
                    // If there's no orientation, default to showing the rotate command.
                    this.SelectedItem = ItemCollection.OfType<ComboBoxItem>().FirstOrDefault(i => i.Text == RotateCommandText);
                }

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
        /// Handles the dropdown selection. Only triggers the tool if the specific "Rotate" command is chosen.
        /// </summary>
        protected override async void OnSelectionChange(ComboBoxItem item)
        {
            if (_isUpdating || item == null || string.IsNullOrWhiteSpace(item.Text))
            {
                return;
            }

            // Requirement 4: Only launch if the new Rotate item is selected.
            if (item.Text == RotateCommandText)
            {
                await RunRotateToolAsync();
            }
        }

        /// <summary>
        /// Requirement 1: This method does nothing.
        /// </summary>
        protected override void OnEnter()
        {
            // Per requirements, do nothing on Enter.
            return;
        }

        /// <summary>
        /// Requirement 5: Runs the "rotatePhoto" tool with "true" as the argument.
        /// </summary>
        private async Task RunRotateToolAsync()
        {
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string toolBoxPath = Path.Combine(assemblyDir, "PythonScripts", "PhotologToolbar.pyt");
            string toolName = $"{toolBoxPath}\\rotatePhoto"; // New tool name

            if (!File.Exists(toolBoxPath))
            {
                MessageBox.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }

            // New argument: a single string "true"
            var args = Geoprocessing.MakeValueArray("true");

            await QueuedTask.Run(async () =>
            {
                var result = await Geoprocessing.ExecuteToolAsync(toolName, args, null, CancellationToken.None, null, GPExecuteToolFlags.Default);

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

            // After the tool runs, refresh the UI to show the new orientation value.
            await UpdateComboAsync();
        }
        #endregion
    }
}

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
using System.Text.RegularExpressions; // Required for Regex
using System.Threading;
using System.Threading.Tasks;

#nullable enable

namespace PhotoLogToolbar
{
    /// <summary>
    /// ComboBox3 - Refactored with user-friendly headings and clean numeric display.
    /// </summary>
    internal class ComboBox3 : ComboBox
    {
        private bool _isUpdating = false;
        private readonly Dictionary<string, string> _standardHeadings = new Dictionary<string, string>
        {
            { "N", "0" }, { "NE", "45" }, { "E", "90" }, { "SE", "135" },
            { "S", "180" }, { "SW", "225" }, { "W", "270" }, { "NW", "315" }
        };

        #region Constructor / lifecycle

        public ComboBox3()
        {
            _ = UpdateComboAsync();
            MapSeriesWatcher.Instance.Subscribe(OnMapSeriesPageChanged);
            MapLayoutWatcher.Instance.Subscribe(OnLayoutChanged);
        }

        ~ComboBox3()
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
                    Text = "N/A";
                    Enabled = false;
                    return;
                }

                var currentPageValue = await GetCurrentMapSeriesIndexValueAsync();
                string? currentFeatureValue = null;

                await QueuedTask.Run(() =>
                {
                    if (!string.IsNullOrEmpty(currentPageValue))
                    {
                        var qf = new QueryFilter { WhereClause = $"{QuoteFieldForFileGdb("Number")} = {EscapeForSql(currentPageValue)}", SubFields = "Heading" };
                        using (var cursor = featureLayer.Search(qf))
                        {
                            if (cursor.MoveNext())
                            {
                                currentFeatureValue = cursor.Current["Heading"]?.ToString();
                            }
                        }
                    }
                });

                // Populate the dropdown with user-friendly annotated headings.
                foreach (var heading in _standardHeadings)
                {
                    Add(new ComboBoxItem($"{heading.Key} - {heading.Value}"));
                }

                // ✅ CHANGED: Always display the raw numeric value in the text box.
                this.Text = currentFeatureValue ?? "";

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

        protected override async void OnSelectionChange(ComboBoxItem item)
        {
            if (_isUpdating || item == null || string.IsNullOrWhiteSpace(item.Text))
            {
                return;
            }
            await ProcessAndRunTool(item.Text);
        }

        protected override async void OnEnter()
        {
            if (_isUpdating || string.IsNullOrWhiteSpace(this.Text))
            {
                return;
            }
            await ProcessAndRunTool(this.Text);
        }

        private async Task ProcessAndRunTool(string rawText)
        {
            string numericValue = rawText;

            // This logic correctly extracts the number from either a friendly name ("S - 180")
            // or a plain number ("180").
            var match = Regex.Match(rawText, @"- (\d+)");
            if (match.Success)
            {
                numericValue = match.Groups[1].Value;
            }

            await RunGeoprocessingTool(numericValue);
        }

        private async Task RunGeoprocessingTool(string fieldValue)
        {
            string fieldName = "Heading";
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string toolBoxPath = Path.Combine(assemblyDir, "PythonScripts", "PhotologToolbar.pyt");
            string toolName = $"{toolBoxPath}\\EditField";

            if (!File.Exists(toolBoxPath))
            {
                MessageBox.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }

            var args = Geoprocessing.MakeValueArray(fieldName, fieldValue);

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

            // The refresh call will now correctly set the text to the new numeric value.
            await UpdateComboAsync();
        }
        #endregion
    }
}

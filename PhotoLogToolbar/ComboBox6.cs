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
    /// ComboBox6 - Refactored for stability and to handle the free-form 'Comment' field.
    /// </summary>
    internal class ComboBox6 : ComboBox
    {
        private bool _isUpdating = false;

        #region Constructor / lifecycle

        public ComboBox6()
        {
            _ = UpdateComboAsync();
            MapSeriesWatcher.Instance.Subscribe(OnMapSeriesPageChanged);
            MapLayoutWatcher.Instance.Subscribe(OnLayoutChanged);
        }

        ~ComboBox6()
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
                // Since there's no dropdown list, we only need to update the text.
                Clear();

                var featureLayer = MapView.Active?.Map?.GetLayersAsFlattenedList()
                                       .OfType<FeatureLayer>()
                                       .FirstOrDefault(fl => fl.Name.Equals("Photo Location"));

                if (featureLayer == null)
                {
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
                        var qf = new QueryFilter { WhereClause = $"{QuoteFieldForFileGdb("Number")} = {EscapeForSql(currentPageValue)}", SubFields = "Comment" };
                        using (var cursor = featureLayer.Search(qf))
                        {
                            if (cursor.MoveNext())
                            {
                                currentFeatureValue = cursor.Current["Comment"]?.ToString();
                            }
                        }
                    }
                });

                // Simply display the current comment value.
                this.Text = currentFeatureValue ?? string.Empty;
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
        /// This control has no dropdown items to select, so this method is not used.
        /// </summary>
        protected override void OnSelectionChange(ComboBoxItem item)
        {
            return;
        }

        /// <summary>
        /// Fires when the user presses Enter or clicks away after typing a new comment.
        /// </summary>
        protected override async void OnEnter()
        {
            if (_isUpdating || this.Text == null) // Check for null, not just whitespace, as a null comment is valid
            {
                return;
            }

            await RunGeoprocessingTool(this.Text);
        }

        /// <summary>
        /// Runs the geoprocessing tool to update the 'Comment' field.
        /// </summary>
        private async Task RunGeoprocessingTool(string fieldValue)
        {
            string fieldName = "Comment";
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

            // After the tool runs, refresh the UI.
            await UpdateComboAsync();
        }
        #endregion
    }
}

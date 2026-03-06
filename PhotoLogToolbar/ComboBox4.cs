using ArcGIS.Core.Data;
// The incorrect 'using ArcGIS.Core.Geoprocessing;' has been removed.
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Core.Geoprocessing; // This is the correct one.
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
    /// ComboBox4
    /// </summary>
    internal class ComboBox4 : ComboBox
    {
        private bool _isUpdating = false;

        #region Constructor / lifecycle

        public ComboBox4()
        {
            _ = UpdateComboAsync();
            MapSeriesWatcher.Instance.Subscribe(OnMapSeriesPageChanged);
            MapLayoutWatcher.Instance.Subscribe(OnLayoutChanged);
        }

        ~ComboBox4()
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

                await QueuedTask.Run(() =>
                {
                    var uniqueValues = new HashSet<string>();
                    if (!string.IsNullOrEmpty(currentPageValue))
                    {
                        var qf = new QueryFilter { WhereClause = $"{QuoteFieldForFileGdb("Number")} = {EscapeForSql(currentPageValue)}", SubFields = "ViewHeight" };
                        using (var cursor = featureLayer.Search(qf))
                        {
                            if (cursor.MoveNext())
                            {
                                currentFeatureValue = cursor.Current["ViewHeight"]?.ToString();
                                if (!string.IsNullOrEmpty(currentFeatureValue)) uniqueValues.Add(currentFeatureValue);
                            }
                        }
                    }

                    var defaultValues = new[] { "250", "500", "750", "1000", "1500", "2000", "2500", "3000", "3500", "4000", "4500", "5000", "10000", "12500", "15000", "17500", "20000" };
                    foreach (var val in defaultValues) uniqueValues.Add(val);

                    foreach (var item in uniqueValues.OrderBy(v => int.TryParse(v, out int n) ? n : int.MaxValue))
                    {
                        Add(new ComboBoxItem(item));
                    }
                });

                var itemToSelect = ItemCollection.OfType<ComboBoxItem>().FirstOrDefault(i => i.Text == currentFeatureValue);
                if (itemToSelect?.Text == previouslySelectedItem?.Text)
                {
                    this.SelectedItem = previouslySelectedItem;
                }
                else
                {
                    this.SelectedItem = itemToSelect ?? ItemCollection.FirstOrDefault();
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

        protected override async void OnSelectionChange(ComboBoxItem item)
        {
            if (_isUpdating || item == null || string.IsNullOrWhiteSpace(item.Text))
            {
                return;
            }
            await RunGeoprocessingTool(item.Text);
        }

        protected override async void OnEnter()
        {
            if (_isUpdating || string.IsNullOrWhiteSpace(this.Text))
            {
                return;
            }
            await RunGeoprocessingTool(this.Text);
        }

        private async Task RunGeoprocessingTool(string fieldValue)
        {
            string fieldName = "ViewHeight";
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

            await UpdateComboAsync();
        }
        #endregion
    }
}

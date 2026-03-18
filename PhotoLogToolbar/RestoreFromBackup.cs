using ArcGIS.Core.Data;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Core.Geoprocessing;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Dialogs;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Mapping;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using ProMessageBox = ArcGIS.Desktop.Framework.Dialogs.MessageBox;


#nullable enable

namespace PhotoLogToolbar
{
    /// <summary>
    /// The ViewModel for the RestoreBackupDialog.
    /// </summary>
    internal class RestoreBackupViewModel : PropertyChangedBase
    {
        public List<string> AvailableBackupsDisplay { get; private set; } = new List<string>();
        private string? _selectedBackup;
        public string? SelectedBackup { get => _selectedBackup; set => SetProperty(ref _selectedBackup, value); }
        public void LoadBackups(List<BackupManager.BackupInfo> backups)
        {
            if (backups != null && backups.Any())
            {
                AvailableBackupsDisplay = backups.OrderByDescending(b => b.Date)
                                                 .Select(b => b.Date.ToString("yyyy-MM-dd HH:mm:ss"))
                                                 .ToList();
            }
            else { AvailableBackupsDisplay.Add("No backups available"); }
            SelectedBackup = AvailableBackupsDisplay.FirstOrDefault();
            NotifyPropertyChanged(nameof(AvailableBackupsDisplay));
        }
    }

    /// <summary>
    /// The button on the ribbon that launches the restore dialog.
    /// </summary>
    internal class RestoreFromBackupButton : Button
    {
        protected override async void OnClick()
        {
            var backups = await BackupManager.GetAvailableBackupsAsync();
            if (backups == null || !backups.Any())
            {
                ProMessageBox.Show("No backups found. Ensure a map with the 'Photo Location' layer is active.", "Cannot Restore");
                return;
            }

            var vm = new RestoreBackupViewModel();
            vm.LoadBackups(backups);

            var dialogControl = new RestoreBackupDialog { DataContext = vm };
            var window = new Window
            {
                Title = "Restore from Backup",
                Content = dialogControl,
                SizeToContent = SizeToContent.WidthAndHeight,
                WindowStartupLocation = WindowStartupLocation.CenterOwner,
                Owner = FrameworkApplication.Current.MainWindow
            };

            bool? result = window.ShowDialog();

            if (result == true)
            {
                if (vm.SelectedBackup != null && !vm.SelectedBackup.Contains("No backups"))
                {
                    DateTime selectedDate = DateTime.Parse(vm.SelectedBackup);
                    var backupToRestore = backups.FirstOrDefault(b => b.Date == selectedDate);
                    if (backupToRestore != null)
                    {
                        await BackupManager.RestoreBackupAsync(backupToRestore);
                    }
                }
            }
        }

        protected override async void OnUpdate()
        {
            var backups = await BackupManager.GetAvailableBackupsAsync();
            this.Enabled = backups != null && backups.Any();
        }
    }

    /// <summary>
    /// The shared static class for finding and executing backup operations.
    /// </summary>
    internal static class BackupManager
    {
        public static async Task RestoreBackupAsync(BackupInfo backup)
        {
            string backupName = backup.Name;
            string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string toolBoxPath = Path.Combine(assemblyDir, "PythonScripts", "PhotologToolbar.pyt");
            string toolName = $"{toolBoxPath}\\RestoreFromBackup";

            if (!File.Exists(toolBoxPath))
            {
                ProMessageBox.Show($"Toolbox not found at: {toolBoxPath}");
                return;
            }

            var args = Geoprocessing.MakeValueArray(backupName);

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
                    ProMessageBox.Show(sb.ToString(), "Geoprocessing Error");
                }
            });
        }

        public static async Task<List<BackupInfo>?> GetAvailableBackupsAsync()
        {
            return await QueuedTask.Run(() =>
            {
                var layer = MapView.Active?.Map?.GetLayersAsFlattenedList().OfType<FeatureLayer>().FirstOrDefault(fl => fl.Name.Equals("Photo Location"));
                if (layer?.GetFeatureClass().GetDatastore() is not Geodatabase gdb)
                {
                    return null;
                }

                var gdbPath = gdb.GetPath().LocalPath;
                var pattern = new Regex(@"^PhotoPoints_backup_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$");
                var backups = new List<BackupInfo>();

                foreach (var def in gdb.GetDefinitions<FeatureClassDefinition>())
                {
                    var match = pattern.Match(def.GetName());
                    if (match.Success)
                    {
                        var date = new DateTime(
                            int.Parse(match.Groups[1].Value), int.Parse(match.Groups[2].Value), int.Parse(match.Groups[3].Value),
                            int.Parse(match.Groups[4].Value), int.Parse(match.Groups[5].Value), int.Parse(match.Groups[6].Value)
                        );
                        backups.Add(new BackupInfo(def.GetName(), date));
                    }
                }
                return backups;
            });
        }

        public record BackupInfo(string Name, DateTime Date);
    }
}

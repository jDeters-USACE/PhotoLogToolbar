using System.Windows;
using System.Windows.Controls;

namespace PhotoLogToolbar
{
    public partial class RestoreBackupDialog : UserControl
    {
        public RestoreBackupDialog()
        {
            InitializeComponent();
        }

        private void OkButton_Click(object sender, RoutedEventArgs e)
        {
            // Find the parent window and set its DialogResult to true
            Window.GetWindow(this).DialogResult = true;
            Window.GetWindow(this).Close();
        }
    }
}

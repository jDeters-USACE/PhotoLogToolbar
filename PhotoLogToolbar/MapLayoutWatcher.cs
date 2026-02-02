using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Layouts;
using ArcGIS.Desktop.Mapping;
using System;
using System.Timers;
using System.Linq;

namespace PhotoLogToolbar
{
    /// <summary>
    /// Centralized watcher that polls the active layout view and reports when:
    ///  - the active view changes between a LayoutView and other views, or
    ///  - the active layout instance changes (user switched layouts),
    ///  - whether the active layout contains a MapFrame named "Main Map Frame" with a "Photo Location" layer.
    ///
    /// Subscribers receive LayoutChanged events and should respond by repopulating items (one-time)
    /// or disabling the UI when the view is incompatible.
    /// </summary>
    internal sealed class MapLayoutWatcher
    {
        private static readonly Lazy<MapLayoutWatcher> _instance = new(() => new MapLayoutWatcher());
        public static MapLayoutWatcher Instance => _instance.Value;

        private readonly object _lock = new();
        private Timer? _timer;
        private string? _lastLayoutId;
        private bool _lastHasPhotoLocation;
        private bool _lastIsLayoutView;
        private int _subscriberCount;

        /// <summary>
        /// Event invoked when layout state changes.
        /// </summary>
        public event EventHandler<LayoutChangedEventArgs>? LayoutChanged;

        private MapLayoutWatcher() { }

        public void Subscribe(EventHandler<LayoutChangedEventArgs> handler)
        {
            if (handler == null) return;
            lock (_lock)
            {
                LayoutChanged += handler;
                _subscriberCount++;
                if (_subscriberCount == 1)
                    Start();
            }
        }

        public void Unsubscribe(EventHandler<LayoutChangedEventArgs> handler)
        {
            if (handler == null) return;
            lock (_lock)
            {
                LayoutChanged -= handler;
                _subscriberCount = Math.Max(0, _subscriberCount - 1);
                if (_subscriberCount == 0)
                    Stop();
            }
        }

        private void Start()
        {
            if (_timer != null) return;
            _lastLayoutId = null;
            _lastHasPhotoLocation = false;
            _lastIsLayoutView = false;

            _timer = new Timer(750) { AutoReset = true };
            _timer.Elapsed += Timer_Elapsed;
            _timer.Start();
        }

        private void Stop()
        {
            if (_timer == null) return;
            _timer.Stop();
            _timer.Elapsed -= Timer_Elapsed;
            _timer.Dispose();
            _timer = null;
            _lastLayoutId = null;
            _lastHasPhotoLocation = false;
            _lastIsLayoutView = false;
        }

        private async void Timer_Elapsed(object? sender, ElapsedEventArgs e)
        {
            try
            {
                // Read layout/view state on QueuedTask (ArcGIS objects are thread-affine).
                var state = await QueuedTask.Run(() =>
                {
                    var lv = LayoutView.Active;
                    if (lv == null)
                        return new LayoutState(null, false, false);

                    var layout = lv.Layout;
                    if (layout == null)
                        return new LayoutState(null, false, false);

                    // Use a lightweight identifier for the layout instance (hashcode as string).
                    var layoutId = layout.GetHashCode().ToString();

                    // Find the map frame named "Main Map Frame" (if present).
                    var mapFrame = layout.GetElements().OfType<MapFrame>().FirstOrDefault(mf =>
                    {
                        try { return mf.Name == "Main Map Frame"; } catch { return false; }
                    });

                    if (mapFrame == null)
                        return new LayoutState(layoutId, true, false);

                    // Check for the Photo Location feature layer in the map inside that map frame.
                    var hasPhotoLocation = mapFrame?.Map?.GetLayersAsFlattenedList()
                        .OfType<FeatureLayer>()
                        .Any(fl => fl.Name.Equals("Photo Location")) ?? false;

                    return new LayoutState(layoutId, true, hasPhotoLocation);
                }).ConfigureAwait(false);

                // Compare with last-known state; raise event when something changed.
                var layoutIdNow = state.LayoutId;
                var isLayoutViewNow = state.IsLayoutView;
                var hasPhotoNow = state.HasPhotoLocation;

                var changed =
                    layoutIdNow != _lastLayoutId
                    || isLayoutViewNow != _lastIsLayoutView
                    || hasPhotoNow != _lastHasPhotoLocation;

                if (changed)
                {
                    _lastLayoutId = layoutIdNow;
                    _lastIsLayoutView = isLayoutViewNow;
                    _lastHasPhotoLocation = hasPhotoNow;

                    LayoutChanged?.Invoke(this, new LayoutChangedEventArgs(isLayoutViewNow, hasPhotoNow, layoutIdNow));
                }
            }
            catch
            {
                // swallow exceptions to keep polling robust
            }
        }

        private readonly record struct LayoutState(string? LayoutId, bool IsLayoutView, bool HasPhotoLocation);

        /// <summary>
        /// Event args describing layout state.
        /// </summary>
        public sealed class LayoutChangedEventArgs : EventArgs
        {
            public LayoutChangedEventArgs(bool isLayoutView, bool hasPhotoLocation, string? layoutId)
            {
                IsLayoutView = isLayoutView;
                HasPhotoLocation = hasPhotoLocation;
                LayoutId = layoutId;
            }

            public bool IsLayoutView { get; }
            public bool HasPhotoLocation { get; }
            public string? LayoutId { get; }
        }
    }
}
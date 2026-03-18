using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Layouts;
using ArcGIS.Desktop.Mapping;
using System;
using System.Linq;
using System.Threading.Tasks;
using System.Timers;

#nullable enable

namespace PhotoLogToolbar
{
    internal sealed class MapLayoutWatcher
    {
        private static readonly Lazy<MapLayoutWatcher> _instance = new(() => new MapLayoutWatcher());
        public static MapLayoutWatcher Instance => _instance.Value;

        private readonly object _lock = new();
        private Timer? _pollingTimer;
        private Timer? _nudgeTimer;

        private string? _lastLayoutId;
        private bool _lastHasPhotoLocation;
        private bool _lastIsLayoutView;
        private int _subscriberCount;

        public event EventHandler<LayoutChangedEventArgs>? LayoutChanged;

        private MapLayoutWatcher() { }

        public void Subscribe(EventHandler<LayoutChangedEventArgs> handler)
        {
            if (handler == null) return;
            lock (_lock)
            {
                LayoutChanged += handler;
                _subscriberCount++;
                if (_subscriberCount == 1) Start();
            }
        }

        public void Unsubscribe(EventHandler<LayoutChangedEventArgs> handler)
        {
            if (handler == null) return;
            lock (_lock)
            {
                LayoutChanged -= handler;
                _subscriberCount = Math.Max(0, _subscriberCount - 1);
                if (_subscriberCount == 0) Stop();
            }
        }

        private void Start()
        {
            if (_pollingTimer != null) return;
            _lastLayoutId = null;

            _pollingTimer = new Timer(750) { AutoReset = true };
            _pollingTimer.Elapsed += PollingTimer_Elapsed;
            _pollingTimer.Start();

            _nudgeTimer = new Timer(60000) { AutoReset = true };
            _nudgeTimer.Elapsed += NudgeTimer_Elapsed;
            _nudgeTimer.Start();
        }

        private void Stop()
        {
            _pollingTimer?.Stop();
            _pollingTimer?.Dispose();
            _pollingTimer = null;
            _nudgeTimer?.Stop();
            _nudgeTimer?.Dispose();
            _nudgeTimer = null;
        }

        // These methods are called by the UIFocusService and are correct.
        public void PauseNudgeTimer() => _nudgeTimer?.Stop();
        public void ResumeNudgeTimer() => _nudgeTimer?.Start();

        /// <summary>
        /// This method is now separate again.
        /// It bypasses the 'if (changed)' check and ALWAYS fires the event.
        /// </summary>
        public async void ForceRefresh()
        {
            try
            {
                var state = await GetCurrentLayoutState().ConfigureAwait(false);

                // Update the last known state so the next regular poll doesn't fire immediately.
                _lastLayoutId = state.LayoutId;
                _lastIsLayoutView = state.IsLayoutView;
                _lastHasPhotoLocation = state.HasPhotoLocation;

                // Fire the event unconditionally.
                LayoutChanged?.Invoke(this, new LayoutChangedEventArgs(state.IsLayoutView, state.HasPhotoLocation, state.LayoutId));
            }
            catch { /* Swallow */ }
        }

        private void NudgeTimer_Elapsed(object? sender, ElapsedEventArgs e)
        {
            // The nudge timer's only job is to call the true ForceRefresh method.
            ForceRefresh();
        }

        private async void PollingTimer_Elapsed(object? sender, ElapsedEventArgs? e)
        {
            try
            {
                var state = await GetCurrentLayoutState().ConfigureAwait(false);

                var changed = state.LayoutId != _lastLayoutId
                           || state.IsLayoutView != _lastIsLayoutView
                           || state.HasPhotoLocation != _lastHasPhotoLocation;

                if (changed)
                {
                    _lastLayoutId = state.LayoutId;
                    _lastIsLayoutView = state.IsLayoutView;
                    _lastHasPhotoLocation = state.HasPhotoLocation;
                    LayoutChanged?.Invoke(this, new LayoutChangedEventArgs(state.IsLayoutView, state.HasPhotoLocation, state.LayoutId));
                }
            }
            catch { /* Swallow */ }
        }

        private async Task<LayoutState> GetCurrentLayoutState()
        {
            return await QueuedTask.Run(() =>
            {
                var lv = LayoutView.Active;
                if (lv?.Layout == null) return new LayoutState(null, false, false);
                var layout = lv.Layout;
                var layoutId = layout.GetHashCode().ToString();
                var mapFrame = layout.GetElements().OfType<MapFrame>().FirstOrDefault(mf => mf.Name == "Main Map Frame");
                if (mapFrame?.Map == null) return new LayoutState(layoutId, true, false);
                var hasPhotoLocation = mapFrame.Map.GetLayersAsFlattenedList().OfType<FeatureLayer>().Any(fl => fl.Name.Equals("Photo Location"));
                return new LayoutState(layoutId, true, hasPhotoLocation);
            }).ConfigureAwait(false);
        }

        private readonly record struct LayoutState(string? LayoutId, bool IsLayoutView, bool HasPhotoLocation);

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

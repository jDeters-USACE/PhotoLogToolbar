using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Layouts;
using System;
using System.Timers;

#nullable enable

namespace PhotoLogToolbar
{
    /*
     * MapSeriesWatcher.cs
     *
     * PURPOSE:
     *   Provide a single, centralized watcher that polls ArcGIS Pro's MapSeries.CurrentPageNumber
     *   and notifies subscribers when that page number changes. This avoids creating multiple
     *   timers across multiple ComboBox controls and centralizes the thread-affine QueuedTask access
     *   required by ArcGIS Pro SDK objects.
     *
     * DESIGN NOTES (high level conceptual grouping):
     *   - Singleton instance: there is only one watcher for the whole add-in; consumers call
     *     Instance.Subscribe / Instance.Unsubscribe to register.
     *   - Polling loop: uses System.Timers.Timer to run on a thread pool thread. The Timer callback
     *     invokes QueuedTask.Run to safely read MapSeries properties, because Layout/MapSeries are
     *     thread-affine and must be accessed on the QueuedTask.
     *   - Event model: exposes a simple EventHandler&lt;string?&gt; where the payload is the new
     *     CurrentPageNumber value (string) or null if not available. Consumers react to that event
     *     by refreshing UI (for example, calling UpdateComboAsync()).
     *
     * THREADING / LIFECYCLE:
     *   - The Timer itself runs on a thread-pool thread. The reading of ArcGIS objects is executed
     *     on the QueuedTask. The event is raised from the Timer callback (after the QueuedTask
     *     completes). Consumers should ensure their handlers marshal to the UI thread if they touch
     *     WPF controls directly (ComboBox.UpdateComboAsync is already queued appropriately).
     *
     * POLL INTERVAL:
     *   - A reasonable default (750ms) is used. This balances responsiveness with CPU use; change
     *     if your scenario needs faster or slower detection.
     */

    internal sealed class MapSeriesWatcher
    {
        // Lazy singleton instance - ensures single global watcher and deferred creation.
        private static readonly Lazy<MapSeriesWatcher> _instance = new(() => new MapSeriesWatcher());
        public static MapSeriesWatcher Instance => _instance.Value;

        // Simple synchronization lock for subscribe/unsubscribe/start/stop logic.
        private readonly object _lock = new();

        // System.Timers.Timer drives periodic polling. Kept private to control lifecycle.
        private Timer? _timer;

        // Last observed page number (string) so we can detect changes (null = unknown / no map series).
        private string? _lastPageNumber;

        // Track number of subscribers so we can start the timer on first subscriber and stop when none.
        private int _subscriberCount;

        // Public event exposed to subscribers. The string payload is the new CurrentPageNumber (nullable).
        // Using EventHandler<string?> is simple and avoids defining a custom EventArgs type for this single value.
        public event EventHandler<string?>? PageNumberChanged;

        // Private ctor to enforce singleton usage.
        private MapSeriesWatcher() { }

        // Subscribe a handler. The watcher will start polling when the first subscriber registers.
        public void Subscribe(EventHandler<string?> handler)
        {
            if (handler == null) return;

            lock (_lock)
            {
                PageNumberChanged += handler;
                _subscriberCount++;
                if (_subscriberCount == 1)
                    Start();
            }
        }

        // Unsubscribe a previously registered handler. The watcher stops polling when there are no subscribers.
        public void Unsubscribe(EventHandler<string?> handler)
        {
            if (handler == null) return;

            lock (_lock)
            {
                PageNumberChanged -= handler;
                _subscriberCount = Math.Max(0, _subscriberCount - 1);
                if (_subscriberCount == 0)
                    Stop();
            }
        }

        #region Timer lifecycle (Start / Stop)
        // Start the internal timer. This method must be called under _lock.
        private void Start()
        {
            if (_timer != null) return; // guard against double-start

            // Reset last seen value so first poll will always raise an event (if a value exists).
            _lastPageNumber = null;

            // Create the timer. Choosing 750ms as a balanced default.
            _timer = new Timer(750) { AutoReset = true };
            _timer.Elapsed += Timer_Elapsed;
            _timer.Start();
        }

        // Stop the internal timer and clean up event handler to avoid leaks.
        private void Stop()
        {
            if (_timer == null) return;

            _timer.Stop();
            _timer.Elapsed -= Timer_Elapsed;
            _timer.Dispose();
            _timer = null;
            _lastPageNumber = null;
        }
        #endregion

        #region Polling callback
        // Timer callback. Runs on a thread-pool thread. We call QueuedTask.Run to access ArcGIS thread-affine objects.
        // NOTE: the method is async void because it is an event handler for Timer.Elapsed.
        private async void Timer_Elapsed(object? sender, ElapsedEventArgs e)
        {
            try
            {
                // Read MapSeries.CurrentPageNumber on the QueuedTask thread affinity required by ArcGIS objects.
                // We return a string? because ArcGIS returns the CurrentPageNumber as a string.
                var current = await QueuedTask.Run(() =>
                {
                    var lv = LayoutView.Active;
                    return lv?.Layout?.MapSeries?.CurrentPageNumber;
                }).ConfigureAwait(false);

                // If the page number changed since last poll, update state and notify subscribers.
                if (current != _lastPageNumber)
                {
                    _lastPageNumber = current;

                    // Raise the event to notify subscribers. Event invocation is thread-safe here because we
                    // don't modify PageNumberChanged from this thread without locking (subscribe/unsubscribe
                    // already lock).
                    PageNumberChanged?.Invoke(this, current);
                }
            }
            catch
            {
                // Swallow exceptions: we want polling to be robust and continue even if a single poll fails.
                // In production consider logging if you have a safe logging mechanism available.
            }
        }
        #endregion
    }
}
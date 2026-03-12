#nullable enable

namespace PhotoLogToolbar
{
    /// <summary>
    /// A simple static class to hold shared state for the entire ArcGIS Pro session.
    /// </summary>
    internal static class PhotoLogSessionManager
    {
        /// <summary>
        /// Stores the author's name after it has been entered once. This variable
        /// will persist until ArcGIS Pro is closed.
        /// </summary>
        public static string? SessionAuthorName;
    }
}

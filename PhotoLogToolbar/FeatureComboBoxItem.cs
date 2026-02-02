/*

   Copyright 2023 Esri

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

   See the License for the specific language governing permissions and
   limitations under the License.

*/
using ArcGIS.Core.CIM;
using ArcGIS.Core.Geometry;
using ArcGIS.Desktop.Framework.Contracts;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace PhotoLogToolbar
{
  internal class FeatureComboBoxItem : ComboBoxItem
  {
    // Preserve the original constructor and behavior; add a property to store
    // the feature's page key (Number field or other index field used by MapSeries).
    // This makes it safe and explicit to read the page/key back when the user selects an item.
    internal FeatureComboBoxItem (string name, Geometry geometry, string? pageKey = null) : base(name, null, $@"zoom to '{name}'")
    {
      Geometry = geometry;
      PageKey = pageKey ?? name; // default to the display name if no explicit key provided
    }

    // Geometry of the feature (used for zooming)
    internal Geometry Geometry { get; set; }

    // The page key associated with this feature (string). This is the value we will pass to MapSeries.SetCurrentPageNumber.
    // Storing it explicitly avoids relying on ComboBoxItem internals for the displayed text.
    internal string? PageKey { get; }
  }
}

import math
import importlib
import arcpy

# Import Custom Libraries that DO NOT require arcpy
import JLog
importlib.reload(JLog)

def Offset(Lat,Lon,Degrees,Meters=1000):
    # Earth's Radius in meters, sphere
    R = 6378137
    # Offset in Meters
    mLat = math.cos(math.radians(Degrees))*Meters
    mLon = math.sin(math.radians(Degrees))*Meters
    # Coordinate offset in radians
    dLat = mLat/R
    dLon = mLon/(R*math.cos(math.pi*Lat/180))
    # Offset position, decimal degrees
    Lat0 = Lat + dLat * 180/math.pi
    Lon0 = float(Lon) + float(dLon * 180/math.pi)
    del R, mLat, mLon, dLat, dLon
    return Lat0,Lon0

def Simple(photo_location_path, fov_path):
    # Get Spatial Reference
    sr_wgs_1984 = arcpy.SpatialReference(4326) 
    where = None

    # Define Fields for Search Cursor
    fields = ['SHAPE@X',
                'SHAPE@Y',
                'Number',
                'Heading',
                'Orientation',
                'MetersOfView',
                'LongEdgeFOV',
                'ShortEdgeFOV']
    
    # Create search Cursor and gather all selected rows in a list
    photo_location_rows = []
    with arcpy.da.SearchCursor(photo_location_path, fields, where_clause=where) as SC:
        for row in SC:
            photo_location_rows.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]])

    # Define Fields for Search Cursor
    fields = ['SHAPE@', 'Number']
    
    # Create Update Cursor and re-create FOV for each row
    row_number = 0
    with arcpy.da.UpdateCursor(fov_path, fields, where_clause=where) as UC:
        for row in UC:
            # Get all relevant values from the photo_location_row
            X_Coord = photo_location_rows[row_number][0]
            Y_Coord = photo_location_rows[row_number][1]
            Number = photo_location_rows[row_number][2]
            Heading = photo_location_rows[row_number][3]
            Orientation = photo_location_rows[row_number][4]
            MetersOfView = photo_location_rows[row_number][5]
            LongEdgeFOV = photo_location_rows[row_number][6]
            ShortEdgeFOV = photo_location_rows[row_number][7]
            # Advance the row_number for the next row
            row_number += 1

            # Double-check that Number field matches
            if row[1] == Number:
                # Create FOV Polygon
                try:
                    Heading = float(Heading)
                except:
                    # If the heading can't be converted to float, then don't make an FOV polygon
                    Polygon = None
                # If Heading is type 'float', continue creating the FOV
                if isinstance(Heading, float):
                    # Determine Angle of View
                    if Orientation == 'Landscape':
                        AOV = LongEdgeFOV
                    if Orientation == 'Portrait':
                        AOV = ShortEdgeFOV
                    # Duplicating a variable because not using Lat/Lon in the formula below makes my head woozy
                    Lon = float(X_Coord)
                    Lat = float(Y_Coord)
                    # Calculate azmuth for each offset point
                    p1_Degrees = Heading + AOV/2
                    p2_Degrees = Heading - AOV/2
                    # Calculate Hypotenuse Distance
                    HypDist = MetersOfView/(math.cos(math.radians(AOV/2)))
                    # Calculate offset coordinates
                    p1_Coords = Offset(Lat, Lon, p1_Degrees, HypDist)
                    p2_Coords = Offset(Lat, Lon, p2_Degrees, HypDist)
                    # Create Point objects
                    p0 = arcpy.Point(Lon, Lat)
                    p1 = arcpy.Point(p1_Coords[1], p1_Coords[0])
                    p2 = arcpy.Point(p2_Coords[1], p2_Coords[0])
                    # Create point array
                    Array = arcpy.Array([p0, p1, p2, p0])
                    # Create Polygon geometry object
                    Polygon = arcpy.Polygon(Array, sr_wgs_1984)
                    # Memory Cleanup
                    del AOV,Lon,Lat,p1_Degrees,p2_Degrees,HypDist,p1_Coords,p2_Coords,p0,p1,p2,Array
                
                # Update FOV Feature
                row[0] = Polygon
                UC.updateRow(row)
                # Memory Cleanup
                del Polygon
            # Memory Cleanup
            del X_Coord,Y_Coord,Number,Heading,Orientation,MetersOfView,LongEdgeFOV,ShortEdgeFOV

def Main(CurrentPhoto=False):
    L = JLog.PrintLog(Log="C:\\Temp\\PhotoLogToolbar_LOG.txt", Indent=2)
    # Get Spatial Reference
    sr_wgs_1984 = arcpy.SpatialReference(4326) 
    # Reference the project currently open in ArcGIS Pro
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    # Get the active view
    active_view = aprx.activeView
    # Check if the active view is a layout
    if active_view is not None and hasattr(active_view, "pageHeight"):
        # Set the active_layout to the current active_view
        active_layout = active_view
        # Get Map Series Object from the active_layout
        ms = active_layout.mapSeries

        # Get Main Map Frame
        for mf in active_layout.listElements("MAPFRAME_ELEMENT"):
            if "Photo Log - Main" in mf.map.name:

                # Get Photo Location Layer
                for lyr in mf.map.listLayers():
                    if "Photo Location" in lyr.name:

                        # Define Feature Class
                        photo_Location_path = lyr.dataSource

                        # Determine Where Clause
                        if CurrentPhoto:
                            # Get the current page's OID - ms.pageRow provides the attribute row of the current page index
                            current_oid = ms.pageRow.OBJECTID 
                            # Get the OID field name
                            oid_field = arcpy.Describe(photo_Location_path).OIDFieldName
                            # reate a Where Clause to target ONLY this row
                            where = f"{oid_field} = {current_oid}"
                        else:
                            where = None

                        # Define Fields for Search Cursor
                        fields = ['SHAPE@X',
                                    'SHAPE@Y',
                                    'Number',
                                    'Heading',
                                    'Orientation',
                                    'MetersOfView',
                                    'LongEdgeFOV',
                                    'ShortEdgeFOV']
                        
                        # Create search Cursor and gather all selected rows in a list
                        photo_location_rows = []
                        with arcpy.da.SearchCursor(photo_Location_path, fields, where_clause=where) as SC:
                            for row in SC:
                                photo_location_rows.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]])

                        # Get FOV Layer
                        for lyr in mf.map.listLayers():
                            if "Field of View" in lyr.name:

                                # Define Feature Class
                                fov_path = lyr.dataSource

                                # Define Fields for Update Cursor
                                fields = ['SHAPE@', 'Number']
                                
                                # Create Update Cursor and re-create FOV for each row
                                row_number = 0
                                with arcpy.da.UpdateCursor(fov_path, fields, where_clause=where) as UC:
                                    for row in UC:
                                        # Get all relevant values from the photo_location_row
                                        X_Coord = photo_location_rows[row_number][0]
                                        Y_Coord = photo_location_rows[row_number][1]
                                        Number = photo_location_rows[row_number][2]
                                        Heading = photo_location_rows[row_number][3]
                                        Orientation = photo_location_rows[row_number][4]
                                        MetersOfView = photo_location_rows[row_number][5]
                                        LongEdgeFOV = photo_location_rows[row_number][6]
                                        ShortEdgeFOV = photo_location_rows[row_number][7]
                                        # Advance the row_number for the next row
                                        row_number += 1
                                        L.Wrap(f'Row number = {row_number}')
                                        L.SetIndent(4)
                                        L.Wrap(f'X_Coord = {X_Coord}')
                                        L.Wrap(f'Y_coord = {Y_Coord}')
                                        L.Wrap(f'Number = {Number}')
                                        L.Wrap(f'Heading = {Heading}')
                                        L.Wrap(f'Orienttion = {Orientation}')
                                        L.Wrap(f'MetersOfView = {MetersOfView}')
                                        L.Wrap(f'LongEdgeFOV = {LongEdgeFOV}')
                                        L.Wrap(f'ShortEdgeFOV = {ShortEdgeFOV}')
                                        # Double-check that Number field matches
                                        if row[1] == Number:
                                            # Create FOV Polygon
                                            L.Wrap('Recreating Field of View Polygon for Photograph {Number}...')
                                            try:
                                                Heading = float(Heading)
                                            except:
                                                # If the heading can't be converted to float, then don't make an FOV polygon
                                                Polygon = None
                                            # If Heading is type 'float', continue creating the FOV
                                            if isinstance(Heading, float):
                                                # Determine Angle of View
                                                if Orientation == 'Landscape':
                                                    AOV = LongEdgeFOV
                                                if Orientation == 'Portrait':
                                                    AOV = ShortEdgeFOV
                                                # Duplicating a variable because not using Lat/Lon in the formula below makes my head woozy
                                                Lon = float(X_Coord)
                                                Lat = float(Y_Coord)
                                                # Calculate azmuth for each offset point
                                                p1_Degrees = Heading + AOV/2
                                                p2_Degrees = Heading - AOV/2
                                                # Calculate Hypotenuse Distance
                                                HypDist = MetersOfView/(math.cos(math.radians(AOV/2)))
                                                # Calculate offset coordinates
                                                p1_Coords = Offset(Lat, Lon, p1_Degrees, HypDist)
                                                p2_Coords = Offset(Lat, Lon, p2_Degrees, HypDist)
                                                # Create Point objects
                                                p0 = arcpy.Point(Lon, Lat)
                                                p1 = arcpy.Point(p1_Coords[1], p1_Coords[0])
                                                p2 = arcpy.Point(p2_Coords[1], p2_Coords[0])
                                                # Create point array
                                                Array = arcpy.Array([p0, p1, p2, p0])
                                                L.Wrap(f'[[{Lon}, {Lat}], [{p1_Coords[1]}, {p1_Coords[0]}], [{p2_Coords[1]}, {p2_Coords[0]}], [[{Lon}, {Lat}]]]')
                                                # Create Polygon geometry object
                                                Polygon = arcpy.Polygon(Array, sr_wgs_1984)
                                                # Memory Cleanup
                                                del AOV,Lon,Lat,p1_Degrees,p2_Degrees,HypDist,p1_Coords,p2_Coords,p0,p1,p2,Array
                                            
                                            # Update FOV Feature
                                            row[0] = Polygon
                                            UC.updateRow(row)
                                            L.SetIndent(2)
                                            # Memory Cleanup
                                            del Polygon
                                        # Memory Cleanup
                                        del X_Coord,Y_Coord,Number,Heading,Orientation,MetersOfView,LongEdgeFOV,ShortEdgeFOV

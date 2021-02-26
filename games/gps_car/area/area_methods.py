from shapely.geometry import Point, Polygon, LinearRing
from shapely.ops import nearest_points
from math import radians, cos, sin, asin, sqrt

def in_valid_area(game_area, location):
    boundary_area = Polygon(game_area.area)
    loc = Point([location.lon, location.lat])
    """Returns True if inside the valid area, False if not"""
    print("BOUNDARY AREA BOOLEAN: ",boundary_area.contains(loc))
    print("GAME AREA BOOLEAN: " , game_area.reversed)
    ans = boundary_area.contains(loc) is game_area.reversed
    return ans

def distance_to_border(game_area, location):
    border = LinearRing(game_area.area)
    loc = Point([location.lon, location.lat])
    p1, _ = nearest_points(border, loc)

    def haversine(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371000
        return c * r

    distance = haversine(loc.x, loc.y, p1.x, p1.y)
    return distance

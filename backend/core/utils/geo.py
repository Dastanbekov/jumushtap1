"""
Utility functions for geolocation calculations.
Used for job matching and check-in validation.
"""

import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    
    Returns distance in kilometers.
    
    Args:
        lat1 (float): Latitude of point 1
        lon1 (float): Longitude of point 1
        lat2 (float): Latitude of point 2
        lon2 (float): Longitude of point 2
    
    Returns:
        float: Distance in kilometers
    
    Example:
        >>> haversine_distance(42.8746, 74.5698, 42.8800, 74.5800)
        0.96  # ~960 meters
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (
        math.sin(dlat / 2)**2 + 
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    )
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance


def is_within_radius(lat1, lon1, lat2, lon2, radius_km):
    """
    Check if two points are within a specified radius.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        radius_km (float): Maximum distance in kilometers
    
    Returns:
        bool: True if points are within radius
    
    Example:
        >>> is_within_radius(42.8746, 74.5698, 42.8800, 74.5800, 1.0)
        True  # Within 1km
    """
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    return distance <= radius_km


def validate_coordinates(lat, lng):
    """
    Validate latitude and longitude values.
    
    Args:
        lat (float): Latitude (-90 to 90)
        lng (float): Longitude (-180 to 180)
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        >>> validate_coordinates(42.8746, 74.5698)
        (True, None)
        >>> validate_coordinates(100, 74.5698)
        (False, 'Invalid latitude: must be between -90 and 90')
    """
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return False, 'Coordinates must be numeric'
    
    if not (-90 <= lat <= 90):
        return False, f'Invalid latitude: must be between -90 and 90, got {lat}'
    
    if not (-180 <= lng <= 180):
        return False, f'Invalid longitude: must be between -180 and 180, got {lng}'
    
    return True, None


def calculate_bounding_box(lat, lon, radius_km):
    """
    Calculate bounding box for a circle defined by center point and radius.
    Used for efficient database queries (filter by lat/lng range before haversine).
    
    Args:
        lat (float): Center latitude
        lon (float): Center longitude
        radius_km (float): Radius in kilometers
    
    Returns:
        dict: {'min_lat', 'max_lat', 'min_lng', 'max_lng'}
    
    Example:
        >>> box = calculate_bounding_box(42.8746, 74.5698, 5.0)
        >>> box['min_lat']
        42.829...
    """
    # Approximate degrees for given radius
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 km * cos(latitude)
    
    lat_rad = math.radians(lat)
    
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * math.cos(lat_rad))
    
    return {
        'min_lat': lat - lat_delta,
        'max_lat': lat + lat_delta,
        'min_lng': lon - lng_delta,
        'max_lng': lon + lng_delta,
    }

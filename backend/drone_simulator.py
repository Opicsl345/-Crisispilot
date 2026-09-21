import math

# Remote Drone Airbase (Placed outside the city center for realistic deployment)
DRONE_BASE_LAT = 27.7500
DRONE_BASE_LON = 85.4000

def calculate_flight_path(target_lat, target_lon):
    """Calculates distance, heading, and simulated flight telemetry for drone dispatch."""
    # Haversine approximation for distance in km
    R = 6371.0
    dlat = math.radians(target_lat - DRONE_BASE_LAT)
    dlon = math.radians(target_lon - DRONE_BASE_LON)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(DRONE_BASE_LAT)) * math.cos(math.radians(target_lat)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = R * c

    # Estimated flight time assuming 60 km/h drone speed
    flight_time_minutes = round((distance_km / 60.0) * 60, 1)
    battery_drain_percent = round(distance_km * 4, 1) # Estimated drain rate

    return {
        "base_station": {"lat": DRONE_BASE_LAT, "lon": DRONE_BASE_LON},
        "target": {"lat": target_lat, "lon": target_lon},
        "distance_km": round(distance_km, 2),
        "eta_minutes": flight_time_minutes,
        "battery_required_percent": battery_drain_percent,
        "status": "DISPATCHED_FROM_REMOTE_HANGAR"
    }
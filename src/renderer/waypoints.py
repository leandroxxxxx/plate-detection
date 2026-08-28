"""
waypoints.py

JSON waypoint parsing and smooth interpolation utilities.
"""

import json
import os


def load_waypoints(path):
    """Load waypoints from JSON and normalize timestamp t to [0, 1]."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Waypoints file not found: {path}")

    with open(path, "r") as f:
        waypoints = json.load(f)

    if not isinstance(waypoints, list) or len(waypoints) < 2:
        raise ValueError("Waypoints must be a list with at least 2 entries.")

    required_keys = {"t", "azimuth", "elevation", "distance"}
    for i, wp in enumerate(waypoints):
        if not required_keys.issubset(wp.keys()):
            raise KeyError(f"Waypoint {i} is missing keys. Required: {required_keys}")
        wp.setdefault("pan_x", 0.0)
        wp.setdefault("pan_y", 0.0)
        wp.setdefault("pan_z", 0.0)

    waypoints.sort(key=lambda wp: wp["t"])

    t_vals = [wp["t"] for wp in waypoints]
    t_min, t_max = t_vals[0], t_vals[-1]
    t_range = t_max - t_min
    if t_range == 0:
        raise ValueError("All waypoints have the same t value.")

    for wp in waypoints:
        wp["t"] = (wp["t"] - t_min) / t_range

    return waypoints


def smoothstep(edge0, edge1, x):
    """Hermite smooth interpolation between edge0 and edge1."""
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    """Linear interpolation."""
    return a + (b - a) * t


def sample_waypoints(waypoints, t):
    """Interpolate (azimuth, elevation, distance, pan_x, pan_y, pan_z) at normalized time t."""
    t = max(0.0, min(1.0, t))

    for i in range(len(waypoints) - 1):
        wp_a = waypoints[i]
        wp_b = waypoints[i + 1]
        if wp_a["t"] <= t <= wp_b["t"]:
            s = smoothstep(wp_a["t"], wp_b["t"], t)
            azimuth = lerp(wp_a["azimuth"], wp_b["azimuth"], s)
            elevation = lerp(wp_a["elevation"], wp_b["elevation"], s)
            distance = lerp(wp_a["distance"], wp_b["distance"], s)
            pan_x = lerp(wp_a.get("pan_x", 0.0), wp_b.get("pan_x", 0.0), s)
            pan_y = lerp(wp_a.get("pan_y", 0.0), wp_b.get("pan_y", 0.0), s)
            pan_z = lerp(wp_a.get("pan_z", 0.0), wp_b.get("pan_z", 0.0), s)
            return azimuth, elevation, distance, pan_x, pan_y, pan_z

    wp = waypoints[-1]
    return (
        wp["azimuth"],
        wp["elevation"],
        wp["distance"],
        wp.get("pan_x", 0.0),
        wp.get("pan_y", 0.0),
        wp.get("pan_z", 0.0),
    )
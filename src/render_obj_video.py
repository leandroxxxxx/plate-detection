"""
render_obj_video.py

Imports an .obj file into Blender, creates an animated camera (orbiting
around the object while varying angle and distance) and renders an MP4
video of N seconds.

USAGE (command line, outside Blender):
    blender --background --python render_obj_video.py -- \
        --obj outputs/texto_3d.obj \
        --out outputs/video.mp4 \
        --duration 10 \
        --fps 30

Requirements:
    - Blender installed (3.6+ recommended; written with 4.x in mind)
    - No extra Python dependencies: everything runs inside Blender's own bpy

Note on versions:
    - Blender >= 3.6/4.x: import via bpy.ops.wm.obj_import
    - Blender < 3.6 (legacy): import via bpy.ops.import_scene.obj
    The script automatically detects which operator is available.
"""

import bpy
import math
import json
import argparse
import sys
import os


# ---------------------------------------------------------------------------
# Blender version helpers
# ---------------------------------------------------------------------------
def blender_version():
    """Return (major, minor) tuple, e.g. (4, 0) for Blender 4.0."""
    return (bpy.app.version[0], bpy.app.version[1])


def default_engine():
    """
    BLENDER_EEVEE_NEXT is only available as a non-experimental engine
    from Blender 4.1 onward.  On 4.0 and earlier we fall back to the
    legacy BLENDER_EEVEE.
    """
    if blender_version() >= (4, 1):
        return "BLENDER_EEVEE_NEXT"
    return "BLENDER_EEVEE"


# ---------------------------------------------------------------------------
# Argument parsing (separating Blender's own args from the script's args)
# ---------------------------------------------------------------------------
def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser()
    parser.add_argument("--obj", type=str, required=True, help="Path to the .obj file")
    parser.add_argument("--out", type=str, default="outputs/video.mp4", help="Output video path")
    parser.add_argument("--duration", type=float, default=10.0, help="Video duration in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--resolution", type=int, nargs=2, default=[1280, 720], help="Width Height")
    parser.add_argument("--dist-min", type=float, default=2.5, help="Minimum camera distance (multiple of object radius)")
    parser.add_argument("--dist-max", type=float, default=4.0, help="Maximum camera distance")
    parser.add_argument("--orbits", type=float, default=1.0, help="Number of full 360° turns during the video")
    parser.add_argument("--elev-min", type=float, default=10.0, help="Minimum elevation angle in degrees")
    parser.add_argument("--elev-max", type=float, default=55.0, help="Maximum elevation angle in degrees")
    parser.add_argument("--engine", type=str, default=default_engine(),
                        choices=["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"],
                        help="Render engine (EEVEE is faster, CYCLES is more realistic)")
    parser.add_argument("--waypoints", type=str, default=None,
                        help="Path to JSON file with camera waypoints (overrides orbit/elev/dist params)")
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Clear the default scene
# ---------------------------------------------------------------------------
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


# ---------------------------------------------------------------------------
# OBJ import (compatible with both the new and legacy API)
# ---------------------------------------------------------------------------
def import_obj(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"OBJ file not found: {path}")

    if hasattr(bpy.ops.wm, "obj_import"):
        bpy.ops.wm.obj_import(filepath=path)
    else:
        bpy.ops.import_scene.obj(filepath=path)

    imported = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
    if not imported:
        raise RuntimeError("No mesh was imported from the OBJ file.")

    # If there are multiple objects (e.g. each letter separate), join them into one
    if len(imported) > 1:
        bpy.context.view_layer.objects.active = imported[0]
        bpy.ops.object.join()

    obj = bpy.context.view_layer.objects.active
    return obj


def add_black_material(obj):
    """Assign a black diffuse material to the object (characters should be black)."""
    mat = bpy.data.materials.new(name="BlackChars")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)  # black
    # Assign to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def get_object_radius(obj):
    """Return an approximate radius (bounding sphere) to scale the camera."""
    bbox_corners = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [v.x for v in bbox_corners]
    ys = [v.y for v in bbox_corners]
    zs = [v.z for v in bbox_corners]
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)
    return max(dx, dy, dz, 0.01) / 2.0


# ---------------------------------------------------------------------------
# Simple studio lighting (key + fill)
# ---------------------------------------------------------------------------
def setup_lighting(radius):
    key_light_data = bpy.data.lights.new(name="KeyLight", type="AREA")
    key_light_data.energy = 800 * radius
    key_light_data.size = radius * 2
    key_light = bpy.data.objects.new(name="KeyLight", object_data=key_light_data)
    key_light.location = (radius * 2.5, -radius * 2.5, radius * 3)
    bpy.context.collection.objects.link(key_light)

    fill_light_data = bpy.data.lights.new(name="FillLight", type="AREA")
    fill_light_data.energy = 300 * radius
    fill_light_data.size = radius * 3
    fill_light = bpy.data.objects.new(name="FillLight", object_data=fill_light_data)
    fill_light.location = (-radius * 3, -radius * 1.5, radius * 1.5)
    bpy.context.collection.objects.link(fill_light)


# ---------------------------------------------------------------------------
# Waypoint helpers
# ---------------------------------------------------------------------------
def load_waypoints(path):
    """Load waypoints from a JSON file and validate them."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Waypoints file not found: {path}")

    with open(path, "r") as f:
        waypoints = json.load(f)

    if not isinstance(waypoints, list) or len(waypoints) < 2:
        raise ValueError("Waypoints must be a list with at least 2 entries.")

    required_keys = {"t", "azimuth", "elevation", "distance"}
    for i, wp in enumerate(waypoints):
        if not required_keys.issubset(wp.keys()):
            raise KeyError(
                f"Waypoint {i} is missing keys. Required: {required_keys}"
            )

    # Sort by t just in case
    waypoints.sort(key=lambda wp: wp["t"])

    # Normalise t values so the first is 0.0 and the last is 1.0
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
    """Interpolate (azimuth, elevation, distance) at normalised time t."""
    # Clamp t to [0, 1]
    t = max(0.0, min(1.0, t))

    # Find the two surrounding waypoints
    for i in range(len(waypoints) - 1):
        wp_a = waypoints[i]
        wp_b = waypoints[i + 1]
        if wp_a["t"] <= t <= wp_b["t"]:
            # Smoothstep factor between the two waypoints
            s = smoothstep(wp_a["t"], wp_b["t"], t)
            azimuth = lerp(wp_a["azimuth"], wp_b["azimuth"], s)
            elevation = lerp(wp_a["elevation"], wp_b["elevation"], s)
            distance = lerp(wp_a["distance"], wp_b["distance"], s)
            return azimuth, elevation, distance

    # Fallback (shouldn't happen due to clamping)
    return waypoints[-1]["azimuth"], waypoints[-1]["elevation"], waypoints[-1]["distance"]


# ---------------------------------------------------------------------------
# Camera + animation (orbit varying azimuth angle, elevation and distance)
# ---------------------------------------------------------------------------
def setup_camera_animation(target_obj, radius, args, total_frames):
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    # "Track To" makes the camera always look at the object, so we only
    # need to animate its position (orbit), not its rotation directly.
    track = cam.constraints.new(type="TRACK_TO")
    track.target = target_obj
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = total_frames

    # Decide which animation mode to use
    use_waypoints = args.waypoints is not None

    if use_waypoints:
        waypoints = load_waypoints(args.waypoints)
        print(f"[render_obj_video] Loaded {len(waypoints)} waypoints from {args.waypoints}")
    else:
        waypoints = None

    for frame in range(1, total_frames + 1):
        t = (frame - 1) / max(total_frames - 1, 1)  # 0.0 -> 1.0 across the video

        if use_waypoints:
            # Sample from waypoints
            azimuth_deg, elevation_deg, dist_mult = sample_waypoints(waypoints, t)
            azimuth = math.radians(azimuth_deg)
            elevation = math.radians(elevation_deg)
            distance = radius * dist_mult
        else:
            # Original orbit behaviour
            azimuth = math.radians(360.0 * args.orbits * t)
            elevation = math.radians(
                args.elev_min + (args.elev_max - args.elev_min) *
                (0.5 - 0.5 * math.cos(math.pi * t))
            )
            distance = radius * (
                args.dist_min + (args.dist_max - args.dist_min) *
                (0.5 - 0.5 * math.cos(2 * math.pi * t))
            )

        x = distance * math.cos(elevation) * math.cos(azimuth)
        y = distance * math.cos(elevation) * math.sin(azimuth)
        z = distance * math.sin(elevation)

        cam.location = (x, y, z)
        cam.keyframe_insert(data_path="location", frame=frame)

    # Smooth interpolation between keyframes
    if cam.animation_data and cam.animation_data.action:
        for fcurve in cam.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = "AUTO_CLAMPED"
                kp.handle_right_type = "AUTO_CLAMPED"

    return cam


# ---------------------------------------------------------------------------
# Render setup (resolution, fps, video format, encoder)
# ---------------------------------------------------------------------------
def setup_render(args, total_frames):
    scene = bpy.context.scene
    scene.render.engine = args.engine
    scene.render.resolution_x = args.resolution[0]
    scene.render.resolution_y = args.resolution[1]
    scene.render.fps = args.fps
    scene.frame_end = total_frames

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"

    scene.render.filepath = args.out

    # White background
    scene.world = scene.world or bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)  # white


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = parse_args()
    total_frames = int(round(args.duration * args.fps))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)

    clear_scene()
    obj = import_obj(args.obj)
    add_black_material(obj)
    radius = get_object_radius(obj)

    setup_lighting(radius)
    setup_camera_animation(obj, radius, args, total_frames)
    setup_render(args, total_frames)

    print(f"[render_obj_video] Engine: {args.engine} "
          f"(Blender {bpy.app.version_string})")
    print(f"[render_obj_video] Rendering {total_frames} frames "
          f"({args.duration}s @ {args.fps}fps) -> {args.out}")
    bpy.ops.render.render(animation=True)
    print("[render_obj_video] Done.")


if __name__ == "__main__":
    main()
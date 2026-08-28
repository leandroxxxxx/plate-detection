"""
camera.py

Camera creation, focus target (Empty), and keyframe animation generation.
"""

import math
import bpy
from .waypoints import load_waypoints, sample_waypoints


def setup_camera_animation(center, radius, args, total_frames):
    """Set up camera, animated Empty focus target, and keyframes."""
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    # Animated Empty focus target enables true horizontal and vertical camera panning
    cam_target = bpy.data.objects.new("CameraTarget", None)
    bpy.context.collection.objects.link(cam_target)
    cam_target.location = center

    track = cam.constraints.new(type="TRACK_TO")
    track.target = cam_target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = total_frames

    use_waypoints = args.waypoints is not None
    if use_waypoints:
        waypoints = load_waypoints(args.waypoints)
        print(f"[render_obj_video] Loaded {len(waypoints)} waypoints from {args.waypoints}")
        max_dist_mult = max(wp["distance"] for wp in waypoints) + max(
            math.sqrt(wp.get("pan_x", 0.0)**2 + wp.get("pan_y", 0.0)**2 + wp.get("pan_z", 0.0)**2)
            for wp in waypoints
        )
    else:
        waypoints = None
        max_dist_mult = args.dist_max + max(abs(args.pan_x), abs(args.pan_y))

    max_camera_distance = radius * max_dist_mult
    cam.data.clip_start = max(0.0001, max_camera_distance * 0.001)
    cam.data.clip_end = max_camera_distance * 2.0

    for frame in range(1, total_frames + 1):
        t = (frame - 1) / max(total_frames - 1, 1)

        if use_waypoints:
            azimuth_deg, elevation_deg, dist_mult, pan_x, pan_y, pan_z = sample_waypoints(waypoints, t)
            azimuth = math.radians(azimuth_deg)
            elevation = math.radians(elevation_deg)
            distance = radius * dist_mult
        else:
            azimuth = math.radians(360.0 * args.orbits * t)
            elevation = math.radians(
                args.elev_min + (args.elev_max - args.elev_min) * (0.5 - 0.5 * math.cos(math.pi * t))
            )
            distance = radius * (
                args.dist_min + (args.dist_max - args.dist_min) * (0.5 - 0.5 * math.cos(2 * math.pi * t))
            )
            phase = 2.0 * math.pi * args.orbits * t if args.orbits > 0 else 2.0 * math.pi * t
            pan_x = args.pan_x * math.sin(phase)
            pan_y = args.pan_y * math.cos(phase)
            pan_z = 0.0

        rx = math.sin(azimuth)
        ry = -math.cos(azimuth)

        ux = -math.sin(elevation) * math.cos(azimuth)
        uy = -math.sin(elevation) * math.sin(azimuth)
        uz = math.cos(elevation)

        fx = math.cos(elevation) * math.cos(azimuth)
        fy = math.cos(elevation) * math.sin(azimuth)
        fz = math.sin(elevation)

        target_pos = (
            center[0] + (rx * pan_x + ux * pan_y) * radius,
            center[1] + (ry * pan_x + uy * pan_y) * radius,
            center[2] + (uz * pan_y + pan_z) * radius,
        )

        cam_pos = (
            target_pos[0] + fx * distance,
            target_pos[1] + fy * distance,
            target_pos[2] + fz * distance,
        )

        cam_target.location = target_pos
        cam_target.keyframe_insert(data_path="location", frame=frame)

        cam.location = cam_pos
        cam.keyframe_insert(data_path="location", frame=frame)

    for anim_obj in (cam, cam_target):
        if anim_obj.animation_data and anim_obj.animation_data.action:
            for fcurve in anim_obj.animation_data.action.fcurves:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "BEZIER"
                    kp.handle_left_type = "AUTO_CLAMPED"
                    kp.handle_right_type = "AUTO_CLAMPED"

    return cam
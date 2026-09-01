"""
render_engine.py

Configures render resolution, video encoding, color management, and world background.
"""

import bpy
from .config import parse_color


def setup_render(args, total_frames):
    """Configure render settings, output codecs, view transform, and background color."""
    scene = bpy.context.scene
    scene.render.engine = args.engine
    scene.render.resolution_x = args.resolution[0]
    scene.render.resolution_y = args.resolution[1]
    scene.render.fps = args.fps
    scene.frame_end = total_frames

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.filepath = args.out

    # View transform Standard guarantees pure #FFFFFF output without tone-map compression
    if hasattr(scene, "view_settings"):
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"

    # Background color configuration
    scene.world = scene.world or bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = parse_color(args.bg_color)
        if "Strength" in bg.inputs:
            bg.inputs["Strength"].default_value = 1.0
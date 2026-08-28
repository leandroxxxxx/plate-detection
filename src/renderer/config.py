"""
config.py

CLI argument parsing and color conversion utilities.
"""

import argparse
import sys
import bpy


def blender_version():
    """Return (major, minor) tuple, e.g. (4, 0) for Blender 4.0."""
    return (bpy.app.version[0], bpy.app.version[1])


def default_engine():
    """Select the default EEVEE render engine based on Blender version."""
    if blender_version() >= (4, 1):
        return "BLENDER_EEVEE_NEXT"
    return "BLENDER_EEVEE"


def parse_color(color_str):
    """Parse color string ('white', 'black', 'green', or hex '#FFFFFF') to RGBA tuple."""
    color_str = color_str.strip().lower()
    color_presets = {
        "white": (1.0, 1.0, 1.0, 1.0),
        "black": (0.0, 0.0, 0.0, 1.0),
        "green": (0.0, 1.0, 0.0, 1.0),
        "blue": (0.0, 0.0, 1.0, 1.0),
    }
    if color_str in color_presets:
        return color_presets[color_str]
    if color_str.startswith("#"):
        hex_val = color_str.lstrip("#")
        if len(hex_val) == 6:
            r = int(hex_val[0:2], 16) / 255.0
            g = int(hex_val[2:4], 16) / 255.0
            b = int(hex_val[4:6], 16) / 255.0
            return (r, g, b, 1.0)
    return (1.0, 1.0, 1.0, 1.0)


def parse_args():
    """Parse script arguments passed after '--' in Blender command line."""
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Render OBJ animation video in Blender.")
    parser.add_argument("--obj", type=str, required=True, help="Path to the .obj file")
    parser.add_argument("--out", type=str, default="outputs/video.mp4", help="Output video path")
    parser.add_argument("--duration", type=float, default=10.0, help="Video duration in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--resolution", type=int, nargs=2, default=[1280, 720], help="Width Height")
    parser.add_argument("--dist-min", type=float, default=2.5, help="Minimum camera distance (multiple of radius)")
    parser.add_argument("--dist-max", type=float, default=4.0, help="Maximum camera distance")
    parser.add_argument("--orbits", type=float, default=1.0, help="Number of full 360° turns")
    parser.add_argument("--elev-min", type=float, default=10.0, help="Minimum elevation angle in degrees")
    parser.add_argument("--elev-max", type=float, default=55.0, help="Maximum elevation angle in degrees")
    parser.add_argument("--engine", type=str, default=default_engine(),
                        choices=["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"],
                        help="Render engine")
    parser.add_argument("--waypoints", type=str, default=None,
                        help="Path to JSON file with camera waypoints")
    parser.add_argument("--pan-x", type=float, default=0.0,
                        help="Horizontal camera pan amplitude (multiple of object radius)")
    parser.add_argument("--pan-y", type=float, default=0.0,
                        help="Vertical camera pan amplitude (multiple of object radius)")
    parser.add_argument("--bg-color", type=str, default="white",
                        help="Background color ('white', 'green', 'black', or hex '#FFFFFF')")
    return parser.parse_args(argv)
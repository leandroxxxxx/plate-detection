"""
render_obj_video.py

Headless Blender entrypoint orchestrator.
Imports an OBJ file, sets up lighting, animated camera trajectory, and renders video.

USAGE:
    blender --background --python render_obj_video.py -- \
        --obj outputs/texto_3d.obj \
        --out outputs/video.mp4 \
        --duration 10 \
        --fps 30
"""

import os
import sys
import bpy

# Ensure project root and src are available on sys.path inside Blender's Python
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from renderer.config import parse_args
from renderer.scene import clear_scene, import_obj, get_object_bounds, add_black_material
from renderer.lighting import setup_lighting
from renderer.camera import setup_camera_animation
from renderer.render_engine import setup_render


def main():
    args = parse_args()
    total_frames = int(round(args.duration * args.fps))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)

    clear_scene()
    obj = import_obj(args.obj)
    add_black_material(obj)
    center, radius, _ = get_object_bounds(obj)

    setup_lighting(center, radius)
    setup_camera_animation(center, radius, args, total_frames)
    setup_render(args, total_frames)

    print(f"[render_obj_video] Engine: {args.engine} (Blender {bpy.app.version_string})")
    print(f"[render_obj_video] Rendering {total_frames} frames ({args.duration}s @ {args.fps}fps) -> {args.out}")
    bpy.ops.render.render(animation=True)
    print("[render_obj_video] Done.")


if __name__ == "__main__":
    main()
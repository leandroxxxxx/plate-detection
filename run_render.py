"""
run_render.py

Wrapper script that launches Blender headless to render an OBJ video.
Eliminates the need to type the long blender command manually.

Usage:
    python run_render.py
"""

import subprocess
import sys
import os

# ---------------------------------------------------------------------------
# Paths (relative to this script's location)
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
BLENDER_SCRIPT = os.path.join(ROOT, "src", "render_obj_video.py")
OBJ_PATH = os.path.join(ROOT, "outputs", "texto_3d.obj")
OUT_PATH = os.path.join(ROOT, "outputs", "video.mp4")

DURATION = 5
FPS = 8
WAYPOINTS = os.path.join(ROOT, "data", "waypoints.json")   # set to None to use orbit mode

# Orbit-mode camera pan (multiple of object radius). Waypoints can also define
# their own pan_x/pan_y per entry.
PAN_X = 0.0      # horizontal camera pan (multiple of object radius)
PAN_Y = 0.0      # vertical camera pan (multiple of object radius)


def main():
    print(f"[run_render] OBJ file : {OBJ_PATH}")
    print(f"[run_render] Script   : {BLENDER_SCRIPT}")
    print(f"[run_render] Output   : {OUT_PATH}")
    print(f"[run_render] Duration : {DURATION}s @ {FPS}fps")

    # Quick sanity checks
    if not os.path.isfile(OBJ_PATH):
        print(f"[run_render] ERROR: OBJ file not found -> {OBJ_PATH}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(BLENDER_SCRIPT):
        print(f"[run_render] ERROR: Script not found -> {BLENDER_SCRIPT}", file=sys.stderr)
        sys.exit(1)

    cmd = [
        "blender",
        "--background",
        "--python", BLENDER_SCRIPT,
        "--",
        "--obj", OBJ_PATH,
        "--out", OUT_PATH,
        "--duration", str(DURATION),
        "--fps", str(FPS),
    ]

    if WAYPOINTS is not None:
        if not os.path.isfile(WAYPOINTS):
            print(f"[run_render] ERROR: Waypoints file not found -> {WAYPOINTS}", file=sys.stderr)
            sys.exit(1)
        cmd.extend(["--waypoints", WAYPOINTS])
        print(f"[run_render] Waypoints: {WAYPOINTS}")
    else:
        print("[run_render] Waypoints: none (using orbit mode)")

    cmd.extend(["--pan-x", str(PAN_X), "--pan-y", str(PAN_Y)])

    print(f"[run_render] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, shell=False)

    if result.returncode != 0:
        print(f"[run_render] ERROR: Blender exited with code {result.returncode}",
              file=sys.stderr)
        sys.exit(result.returncode)

    print(f"[run_render] Done! Video saved to: {OUT_PATH}")


if __name__ == "__main__":
    main()
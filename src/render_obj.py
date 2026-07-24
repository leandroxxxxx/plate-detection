"""
render_obj.py

Loads a 3D mesh from an OBJ file and renders a preview PNG image
using matplotlib 3D with configurable camera settings.

Usage:
    python src/render_obj.py --obj outputs/texto_3d.obj
"""

import os
import argparse
import trimesh

# --- File Paths ---
# Default input OBJ file path (change this or use --obj)
OBJ_PATH = "outputs/texto_3d.obj"

# --- Camera / Preview Settings ---
# Adjust these values to change the 3D preview appearance
CAMERA_ELEV = 20           # Vertical angle (0 = top-down, 90 = side view)
CAMERA_AZIM = -90          # Horizontal angle (rotation around the object)
CAMERA_DIST = 5          # Zoom multiplier (1.0 = tight fit, larger = more zoomed out)
BOX_ASPECT = [1, 1, 0.6]   # X:Y:Z aspect ratio of the 3D box
FIG_WIDTH = 10             # Figure width in inches
FIG_HEIGHT = 7             # Figure height in inches
PREVIEW_DPI = 150          # Output PNG resolution (dots per inch)
BACKGROUND_COLOR = "#FFFFFF"  # Background color (hex or named)
TEXT_COLOR = "black"       # Mesh color (named or hex)


def render_obj_preview(obj_path: str, output_path: str):
    """
    Load an OBJ file and render a 3D preview PNG using matplotlib.

    Args:
        obj_path: Path to the input .obj file
        output_path: Path for the output .png file
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print(f"[render_obj] Loading: {obj_path}")
    mesh = trimesh.load(obj_path)

    if isinstance(mesh, trimesh.Scene):
        # If the file contains a scene, take the first geometry
        mesh = mesh.dump(concatenate=True)

    print(f"  Vertices: {len(mesh.vertices)}")
    print(f"  Faces:    {len(mesh.faces)}")
    print(f"  Bounds:   {mesh.bounds.tolist()}")

    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), facecolor=BACKGROUND_COLOR)
    ax = fig.add_subplot(111, projection="3d", facecolor=BACKGROUND_COLOR)

    # Render the mesh
    ax.plot_trisurf(
        mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2],
        triangles=mesh.faces,
        color=TEXT_COLOR,
        edgecolor="none",
    )

    ax.set_box_aspect(BOX_ASPECT)
    ax.view_init(elev=CAMERA_ELEV, azim=CAMERA_AZIM)
    ax.set_axis_off()

    # Use CAMERA_DIST as a zoom multiplier on the axis limits
    # (ax.dist is unreliable when set_box_aspect is used)
    margin = CAMERA_DIST
    x_min, x_max = mesh.vertices[:, 0].min(), mesh.vertices[:, 0].max()
    y_min, y_max = mesh.vertices[:, 1].min(), mesh.vertices[:, 1].max()
    z_min, z_max = mesh.vertices[:, 2].min(), mesh.vertices[:, 2].max()
    cx, cy, cz = (x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2
    half_w = max(x_max - x_min, y_max - y_min, z_max - z_min) / 2 * margin
    ax.set_xlim(cx - half_w, cx + half_w)
    ax.set_ylim(cy - half_w, cy + half_w)
    ax.set_zlim(cz - half_w, cz + half_w)
    ax.grid(False)

    # Hide the 3D panes / grid planes
    ax.xaxis.pane.set_visible(False)
    ax.yaxis.pane.set_visible(False)
    ax.zaxis.pane.set_visible(False)

    # Set the entire figure background
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.patch.set_facecolor(BACKGROUND_COLOR)

    plt.savefig(output_path, dpi=PREVIEW_DPI, bbox_inches="tight",
                facecolor=BACKGROUND_COLOR, pad_inches=0)
    plt.close(fig)

    print(f"  Preview:  {output_path}")
    print("[render_obj] Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render a 3D preview PNG from an OBJ file"
    )
    parser.add_argument("--obj", type=str, default=OBJ_PATH, nargs="?",
                        help=f"Path to the input .obj file (default: {OBJ_PATH})")
    parser.add_argument("--output", type=str, default=None,
                        help="Path for the output .png file (default: same name as OBJ)")
    args = parser.parse_args()

    if args.output is None:
        args.output = os.path.splitext(args.obj)[0] + "_preview.png"

    render_obj_preview(args.obj, args.output)
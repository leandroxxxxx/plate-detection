"""
text_to_3d.py

Converts text (e.g. "A1") into a flat 3D mesh using a TrueType font (.ttf),
exports OBJ and GLB files.

Pipeline:
  1. matplotlib.textpath.TextPath  → vector contours (2D) of the text
  2. shapely                       → clean 2D polygons (handles holes like "A", "0")
  3. trimesh.creation.triangulate_polygon → triangulates each polygon
  4. Duplicates faces (front+back) so the flat mesh is visible from both sides
  5. Exports OBJ and GLB
"""

import os
import numpy as np
import trimesh
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon


def text_to_polygons(text: str, font_path: str, size: float = 100.0):
    """
    Convert a string into a list of shapely 2D polygons, properly handling
    holes (e.g. the inner triangle of "A").

    Returns:
        polygons: list[Polygon]
        total_width: float – the advance width of the whole text string
    """
    fp = FontProperties(fname=font_path)
    path = TextPath((0, 0), text, size=size, prop=fp)

    raw_polys = path.to_polygons()
    rings = [np.array(p) for p in raw_polys if len(p) >= 3]

    # Determine which rings are outer contours vs. holes
    outer_indices = []
    for i, ring_a in enumerate(rings):
        poly_a = Polygon(ring_a)
        if not poly_a.is_valid or poly_a.area == 0:
            continue
        is_hole = False
        for j, ring_b in enumerate(rings):
            if i == j:
                continue
            poly_b = Polygon(ring_b)
            if not poly_b.is_valid or poly_b.area == 0:
                continue
            # ring_a is a hole of ring_b if ring_b contains ring_a and is larger
            if poly_b.area > poly_a.area and poly_b.contains(poly_a.buffer(-1e-6)):
                is_hole = True
                break
        if not is_hole:
            outer_indices.append(i)

    result_polygons = []
    for i in outer_indices:
        outer_poly = Polygon(rings[i])
        holes = []
        for j, ring_b in enumerate(rings):
            if i == j:
                continue
            hole_poly = Polygon(ring_b)
            if (outer_poly.area > hole_poly.area and
                    outer_poly.contains(hole_poly.buffer(-1e-6))):
                holes.append(ring_b)
        result_polygons.append(Polygon(outer_poly.exterior.coords, holes))

    total_width = path.get_extents().width
    return result_polygons, total_width


def generate_flat_mesh(text: str, font_path: str, size: float = 100.0, z: float = 0.0):
    """
    Generate a 2-sided flat 3D mesh (trimesh.Trimesh) from text.
    The mesh is centered at the origin (X/Y) for easy camera positioning.

    Returns:
        mesh: trimesh.Trimesh
        total_width: float
    """
    polygons, total_width = text_to_polygons(text, font_path, size)

    all_verts = []
    all_faces = []
    offset = 0

    for poly in polygons:
        if poly.is_empty or poly.area == 0:
            continue

        verts_2d, faces = trimesh.creation.triangulate_polygon(poly)

        verts_3d = np.column_stack(
            [verts_2d, np.full(len(verts_2d), z)]
        )

        front_faces = faces + offset
        back_faces = faces[:, ::-1] + offset   # reversed winding for backface

        all_verts.append(verts_3d)
        all_faces.append(front_faces)
        all_faces.append(back_faces)
        offset += len(verts_3d)

    if not all_verts:
        raise ValueError("No contours generated — check font/text.")

    vertices = np.vstack(all_verts)
    faces = np.vstack(all_faces)

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)

    # Center X/Y around origin (keep Z unchanged)
    center = mesh.centroid.copy()
    center[2] = 0
    mesh.apply_translation(-center)

    return mesh, total_width


def run(text: str = "A1",
        font_path: str = "fonts/FE-Schrift.ttf",
        size: float = 100.0,
        output_dir: str = "outputs"):
    """Main entry point: generate mesh and export OBJ/GLB (no preview)."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"[text_to_3d] Generating mesh for '{text}' using font: {font_path}")
    mesh, width = generate_flat_mesh(text, font_path, size)

    print(f"  Vertices: {len(mesh.vertices)}")
    print(f"  Faces:    {len(mesh.faces)}")
    print(f"  Bounds:   {mesh.bounds.tolist()}")

    # Export OBJ and GLB
    obj_path = os.path.join(output_dir, "texto_3d.obj")
    glb_path = os.path.join(output_dir, "texto_3d.glb")
    mesh.export(obj_path)
    mesh.export(glb_path)
    print(f"  Exported: {obj_path}")
    print(f"  Exported: {glb_path}")

    print("[text_to_3d] Done!")
    return obj_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate 3D mesh from text")
    parser.add_argument("--text", type=str, default="A1", help="Text to render")
    parser.add_argument("--font", type=str, default="fonts/FE-Schrift.ttf",
                        help="Path to .ttf font file")
    parser.add_argument("--size", type=float, default=100.0,
                        help="Font size in arbitrary units")
    parser.add_argument("--output-dir", type=str, default="outputs",
                        help="Output directory")
    args = parser.parse_args()

    run(args.text, args.font, args.size, args.output_dir)
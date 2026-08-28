"""
scene.py

Handles scene cleanup, OBJ mesh importation, bounding calculations, and materials.
"""

import os
import bpy


def clear_scene():
    """Delete all objects and remove orphan data blocks."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def import_obj(path):
    """Import an OBJ file and join mesh parts if necessary."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"OBJ file not found: {path}")

    if hasattr(bpy.ops.wm, "obj_import"):
        bpy.ops.wm.obj_import(filepath=path)
    else:
        bpy.ops.import_scene.obj(filepath=path)

    imported = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
    if not imported:
        raise RuntimeError("No mesh was imported from the OBJ file.")

    if len(imported) > 1:
        bpy.context.view_layer.objects.active = imported[0]
        bpy.ops.object.join()

    return bpy.context.view_layer.objects.active


def get_object_bounds(obj):
    """Return center point (x, y, z), approximate radius, and bounding dimensions."""
    bbox_corners = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [v.x for v in bbox_corners]
    ys = [v.y for v in bbox_corners]
    zs = [v.z for v in bbox_corners]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    center = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0)
    dx = max_x - min_x
    dy = max_y - min_y
    dz = max_z - min_z
    radius = max(dx, dy, dz, 0.01) / 2.0
    return center, radius, (dx, dy, dz)


def add_black_material(obj):
    """Assign a pure matte black material to the object for maximum OCR contrast."""
    mat = bpy.data.materials.new(name="BlackChars")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 1.0
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.0
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = 0.0

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
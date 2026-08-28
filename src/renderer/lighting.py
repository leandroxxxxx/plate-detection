"""
lighting.py

Configures studio key and fill lighting relative to object scale and center.
"""

import bpy


def setup_lighting(center, radius):
    """Create key and fill area lights scaled to object bounding radius."""
    key_light_data = bpy.data.lights.new(name="KeyLight", type="AREA")
    key_light_data.energy = 800 * radius
    key_light_data.size = radius * 2
    key_light = bpy.data.objects.new(name="KeyLight", object_data=key_light_data)
    key_light.location = (center[0] + radius * 2.5, center[1] - radius * 2.5, center[2] + radius * 3)
    bpy.context.collection.objects.link(key_light)

    fill_light_data = bpy.data.lights.new(name="FillLight", type="AREA")
    fill_light_data.energy = 300 * radius
    fill_light_data.size = radius * 3
    fill_light = bpy.data.objects.new(name="FillLight", object_data=fill_light_data)
    fill_light.location = (center[0] - radius * 3, center[1] - radius * 1.5, center[2] + radius * 1.5)
    bpy.context.collection.objects.link(fill_light)
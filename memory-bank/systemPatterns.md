# System Patterns

## Layered Entrypoint Architecture (Blender Headless)

Blender's embedded Python does not always include the project root in `sys.path` when run via `blender --background --python script.py`. The project follows a **thin entrypoint + modular package** pattern:

1. **Thin entrypoint** (`src/render_obj_video.py`, ~53 lines) inserts its own directory into `sys.path`, imports the `renderer` package, and orchestrates the pipeline step by step.
2. **`src/renderer/` subpackage** owns all render rules, split by Single Responsibility (SRP). Each module stays well under ~100 lines.

```
src/
├── render_obj_video.py          # Entrypoint (thin orchestrator)
└── renderer/                    # Render rules package
    ├── __init__.py
    ├── config.py                # CLI arg parsing, color presets/hex, engine selection
    ├── scene.py                 # Scene cleanup, OBJ import, bounds, black material
    ├── camera.py                # Camera, animated Empty target, keyframes, math
    ├── waypoints.py             # JSON loading, validation, lerp/smoothstep sampling
    ├── lighting.py              # Key + Fill studio lights scaled to object
    └── render_engine.py         # Resolution, FFmpeg/H.264, color management, world bg
```

## Render Pipeline (orchestration order in `main()`)

1. `parse_args()` -> `total_frames = round(duration * fps)`
2. `clear_scene()` - remove all objects and orphan data blocks
3. `import_obj()` - import OBJ (handles both `wm.obj_import` and legacy API), joins multiple meshes
4. `add_black_material()` - matte black Principled BSDF (max OCR contrast)
5. `get_object_bounds()` - world-space center, radius, dimensions
6. `setup_lighting(center, radius)` - Key + Fill area lights proportional to radius
7. `setup_camera_animation(center, radius, args, total_frames)` - camera + Empty target + keyframes
8. `setup_render(args, total_frames)` - EEVEE, FFmpeg/H.264, Standard view transform, background
9. `bpy.ops.render.render(animation=True)`

## Camera Model (orbit vs waypoints)

- A camera is created with a `TRACK_TO` constraint aimed at an animated Empty named `CameraTarget`; this enables true horizontal/vertical panning (panning moves the target, not the camera orbit).
- **Orbit mode** (no waypoints): azimuth driven by `orbits`, elevation and distance by cosine easing, optional sinusoidal `pan_x`/`pan_y`.
- **Waypoint mode**: JSON list of `{t, azimuth, elevation, distance, pan_x?, pan_y?, pan_z?}`; `t` normalized to `[0,1]`, sampled via `smoothstep`/`lerp` (Hermite easing between entries).
- Keyframes get `BEZIER` interpolation with `AUTO_CLAMPED` handles.

## Image Generation Pattern

- `main.py` uses a dedicated RNG (`random.Random(seed)`) separate from the plate generator so the sampled effect parameters are reproducible across runs.
- Per-character-string flow: rotate through `versions_per_plate`, apply 3D perspective -> motion blur -> sharpening -> noise -> H.264 simulation, save `.jpg` + `.json` label.
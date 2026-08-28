# Active Context

## Latest Change: Modularization of the Blender Render Pipeline (current focus)

The OBJ-to-MP4 renderer was refactored from a single monolithic script into a thin entrypoint plus a `renderer` package, addressing the specific `sys.path` limitation of Blender headless execution.

**Before:** one file mixing 5 responsibilities (CLI, meshes/materials, camera/waypoints, lighting, render config).

**After:**
- `src/render_obj_video.py` is now a ~53-line orchestrator (entrypoint), keeping imports clean and adding `src/` to `sys.path`.
- New package `src/renderer/` splits responsibilities into:
  - `config.py` (argparse + color presets/hex + EEVEE engine selection)
  - `scene.py` (scene cleanup, OBJ import, bounds, matte black material)
  - `camera.py` (animated camera + Empty target + keyframes)
  - `waypoints.py` (JSON loading, validation, lerp/smoothstep) — pure Python, unit-testable
  - `lighting.py` (Key + Fill studio lights)
  - `render_engine.py` (resolution, FFmpeg, view transform, world background)

**Key behavior preserved / verified:**
- `run_render.py` wrapper remains fully compatible (unchanged entrypoint path `src/render_obj_video.py`).
- Waypoints support (horizontal/vertical camera panning) kept intact.
- Pure white background (`view_transform = "Standard"`) and matte black material retained for OCR detection.

## Worktree State

- Modified: `src/render_obj_video.py`
- Untracked (new): `src/renderer/` (`__init__.py`, `config.py`, `scene.py`, `camera.py`, `waypoints.py`, `lighting.py`, `render_engine.py`)
- No existing memory bank before this session; created fresh `memory-bank/`.

## Open Note / Caveat

`main.py` imports `from src.plate import PlateGenerator` and `from src.plate_generator import RandomPlateGenerator`, but those source files are not currently present in `src/` on this branch (only stale `__pycache__` entries exist; `src/config.py` and `src/utils.py` exist). This suggests a possible work-in-progress or stale state for the image-generation path. Worth confirming before relying on `main.py`.
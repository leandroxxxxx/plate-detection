# Progress

## Completed

- OBJ-to-MP4 Blender render pipeline implemented and functional (`run_render.py` -> `src/render_obj_video.py`).
- Pure white background (`Standard` view transform) + matte black material for OCR detection.
- Horizontal and vertical camera panning with JSON waypoint support (loaded via `data/waypoints.json`).
- **Render pipeline modularized** into `src/renderer/` package with a thin `src/render_obj_video.py` entrypoint; `run_render.py` compatibility retained.
- Synthetic image generation (Mercosul style, FE-Schrift font) with configurable border, effects, and per-image JSON labels.
- Character-pair chunking and batch detection/cropping stages present (`src/crop_plates.py`, `src/detect_and_crop.py`, `src/post_process.py`).

## In Progress / Verification Needed

- Confirm git diff of the renderer refactor is intentional and commit-ready (currently staged as modified entrypoint + untracked `src/renderer/`).
- Validate the refactored entrypoint still runs end-to-end in headless Blender (functional verification not run in this session).
- Resolve the discrepancy where `main.py` imports `src.plate` / `src.plate_generator` but those source files are absent on this branch.

## Planned / Proposed

- Reuse `renderer/` modules for future render scripts (e.g. static-image renders or multi-angle camera) to avoid duplication.
- Add pytest-based unit tests for `src/renderer/waypoints.py` (pure Python, no Blender required).

## Non-Goals (for reference)

- Not a real-time pipeline; it is an offline dataset generator.
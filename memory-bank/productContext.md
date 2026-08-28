# Product Context

## Why This Project Exists

The project produces synthetic data that mirrors real CCTV captures of license plates. It exists because real surveillance footage is hard to label and scarce, while ML models for OCR / detection need large, varied, and precisely labeled datasets.

## Problems It Solves

- **Labeled data at scale**: every generated image ships with a JSON label describing the exact degradation parameters applied, so ground truth is always known.
- **Recovery from plate-wear ambiguity**: generating 1/2/3+ character strings (and 2-char pairs) simulates partially legible plates, useful for training models that recognize plates from partial characters.
- **Realistic camera conditions**: perspective, motion blur, noise, sharpening and codec compression emulate what a real security camera produces, closing the sim-to-real gap.
- **3D animated footage**: the Blender pipeline turns a static OBJ into animated multi-angle video (orbit or scripted waypoints) with clean OCR-friendly rendering (pure white background, matte black characters), enabling video-level detection experiments.

## User Experience / Workflow

1. Configure generation in `data/inputs.json` (counts, chars, seeds, effect ranges).
2. Run `main.py` to produce image + label files under `generated-images/`.
3. Optionally run the pair-chunk stage (`src/crop_plates.py` / `src/detect_and_crop.py`).
4. For video, configure constants at the top of `run_render.py` (paths, duration, fps, waypoints, pan, bg color) and run it. It shells out to headless Blender, which loads `src/render_obj_video.py`.
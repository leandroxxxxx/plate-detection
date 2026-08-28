# Tech Stack

- **Language**: Python 3
- **Main dependency**: Pillow >= 10.0.0 (`requirements.txt`)
- **External tool**: Blender 4.x (headless) for the 3D video render pipeline. Runs via `blender --background --python ...`; EEVEE is the default engine (`BLENDER_EEVEE_NEXT` on Blender >= 4.1, `BLENDER_EEVEE` otherwise). Cycles also selectable via `--engine`.
- **Format/spec of interest**: Mercosul license plate style; FE-Schrift font for characters; outputs as `.jpg` images with `.json` labels.
- **3D assets**: OBJ input (`outputs/texto_3d.obj`), synthesized from text (via `src/text_to_3d.py` / `src/render_obj.py`).
- **Video output**: MPEG4 / H.264 (`ffmpeg` container handled by Blender), default MP4.
- **Data config**: JSON files under `data/` (`inputs.json` for generation, `waypoints.json` for camera paths).
- **Testing**: ad-hoc scripts under `test/` (e.g. `run_test.py`); no pytest dependency currently declared.
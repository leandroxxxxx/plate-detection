# Decisions Log

| Decision | Details |
| :--- | :--- |
| Thin entrypoint for Blender headless | `src/render_obj_video.py` must not contain heavy logic; it guarantees `sys.path` and orchestrates only. Reason: Blender's embedded interpreter may not include the project root in `sys.path`. |
| Modular `renderer/` package (SRP) | Split CL/config, scene/meshes, camera, waypoints, lighting, and render-engine into separate modules so no file exceeds ~100 lines and each has one responsibility. |
| `view_transform = "Standard"` | Guarantees pure `#FFFFFF` output without tone-map compression, improving OCR contrast. Decided at commit "enable pure white background and matte black material for OCR detection". |
| Matte black material | Characters rendered as matte black for maximum contrast against the white background in OCR workflows. |
| Animated Empty `CameraTarget` + `TRACK_TO` | Enables true horizontal and vertical camera panning (the target moves; the camera tracks it). Decided at commit "implement horizontal and vertical camera panning with waypoint support". |
| Waypoint interpolation | JSON waypoints normalized to `t in [0,1]` and sampled with `smoothstep`/`lerp` (Hermite easing) between entries for smooth camera motion. |
| EEVEE engine selection by version | `BLENDER_EEVEE_NEXT` when Blender >= 4.1, else `BLENDER_EEVEE`; the engine default is computed at runtime. |

## Rejected / Not Applied

- (None recorded yet. Future candidates: alternative render engines, static-image renderer reusing `renderer/` modules to avoid duplication.)
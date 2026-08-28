# Project Brief - plate-detection

## Purpose

Synthetic dataset generator for OCR / character-detection work targeting license plates worn by surveillance (CCTV) cameras. The project creates character strings in the Mercosul license-plate style, applies realistic camera-degradation effects, and provides a 3D video render pipeline to produce animated footage of a plate model for further detection experiments.

## Core Capabilities

1. **Synthetic image generation** (1, 2, 3+ characters) rendered in the Mercosul style with the FE-Schrift font on a white background, plus an optional gray border.
2. **Degradation pipeline** simulating CCTV footage: 3D perspective (pitch/yaw/roll), motion blur, sharpening, noise, and simulated H.264 compression. Each variation is saved as an image plus a JSON label with the applied parameters.
3. **Character-pair chunking** (optional second stage) that extracts consecutive character pairs from generated images for detection-model training.
4. **3D render pipeline**: converts a text OBJ into an animated MP4 using Blender headless, with a configurable animated camera (orbit or waypoint-driven), studio lighting, and OCR-friendly pure white background + matte black material.

## Entry Points

| Entry point | Purpose |
| :--- | :--- |
| `main.py` | Image-generation orchestration (loads `data/inputs.json`). |
| `run_render.py` | Wrapper that launches Blender headless to render an OBJ video. |
| `src/render_obj_video.py` | Thin Blender entrypoint that orchestrates the render pipeline. |
| `src/render_obj.py` | Alternate standalone 3D preview render script (configurable camera). |

## Current Branch

- Branch: `experiment/3d-cctv-pipeline`
- Remote: `https://github.com/leandroxxxxx/plate-detection.git`

## Language Policy

Per project coding standards, all code, comments, docs, and commit messages are written in **English** only. Portuguese is allowed only in chat conversation with the user.
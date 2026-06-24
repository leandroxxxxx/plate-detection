# Synthetic Mercosur License Plate Generator

This project generates synthetic Brazilian license plate images following the Mercosur standard and creates degraded variations that simulate security camera footage. It can be used to build datasets for OCR, license plate detection, and image-processing tests.

For each license plate, the project:

1. generates a random identifier in the `LLLNLNN` format;
2. renders the plate with a blue header, custom font, and watermark;
3. creates multiple versions with randomized parameters;
4. applies motion blur, sharpening, noise, and simulated H.264 compression;
5. saves the image and a JSON label containing the applied parameters.

An optional second stage extracts consecutive character pairs from each plate. Perspective distortion and rotation are applied independently to each extracted pair, simulating variations from elevated security cameras without distorting the complete plate image.

## Requirements

- Python 3
- Pillow 10 or newer

Install the dependencies in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Image generation is controlled by `data/inputs.json`:

```json
{
    "num_plates": 1,
    "versions_per_plate": 3,
    "seed": 42,
    "effects": {
        "perspective": {
            "camera_elevation_range": [30, 60],
            "horizontal_angle_range": [-15, 15]
        },
        "rotation": {
            "angle_range": [-5, 5]
        },
        "motion_blur": {
            "angle_range": [10, 20],
            "intensity_range": [3, 7]
        },
        "sharpening": {
            "percent_range": [150, 210]
        },
        "noise": {
            "intensity_range": [0.03, 0.07]
        },
        "h264": {
            "degradation_level_range": [80, 90]
        }
    },
    "output_dir": "generated-images"
}
```

Main options:

- `num_plates`: number of different license plates to generate.
- `versions_per_plate`: number of variations generated for each plate.
- `seed`: controls license plate generation and parameter randomization.
- `output_dir`: directory where images and labels are saved.
- `camera_elevation_range`: vertical camera angle independently applied to each character pair. The default 30–60° range simulates cameras mounted above vehicles.
- `horizontal_angle_range`: lateral perspective angle independently applied to each pair.
- `rotation.angle_range`: independent in-plane rotation for each pair. A moderate ±5° avoids unrealistic diagonal crops.
- `angle_range`: motion blur angle range, in degrees.
- `intensity_range`: motion blur or noise intensity range, depending on the effect.
- `percent_range`: sharpening strength range.
- `degradation_level_range`: compression degradation range.

Integer boundaries are inclusive. For example, `[3, 7]` can produce 3, 4, 5, 6, or 7. Decimal values can assume any value within the configured range.

The total number of generated images is:

```text
num_plates × versions_per_plate
```

## Usage

Run the following command from the project root:

```bash
python3 main.py
```

With the example configuration, the program generates one license plate and three variations of it.

## Generated Files

The output is separated into images and labels:

```text
generated-images/
├── plates/
│   ├── placa_RAG3E76_v01.jpg
│   ├── placa_RAG3E76_v02.jpg
│   └── placa_RAG3E76_v03.jpg
└── labels/
    ├── placa_RAG3E76_v01.json
    ├── placa_RAG3E76_v02.json
    └── placa_RAG3E76_v03.json
```

Each image and its label share the same base filename. A label has the following structure:

```json
{
    "plate": "RAG3E76",
    "version": 1,
    "motion_blur": {
        "angle": 16.39426798457884,
        "intensity": 3
    },
    "sharpening": {
        "percent": 197
    },
    "noise": {
        "intensity": 0.04100117273476477
    },
    "h264": {
        "degradation_level": 83
    }
}
```

## Applied Effects

- **Perspective distortion (character pairs only):** simulates vertical foreshortening and trapezoidal distortion caused by a camera mounted above and to the side of a vehicle.
- **Rotation (character pairs only):** adds a small in-plane camera or vehicle alignment variation while preserving the crop dimensions.
- **Motion blur:** overlays shifted copies of the image to simulate movement.
- **Sharpening:** enhances edges and creates halos similar to those produced by security cameras.
- **Noise:** blends the image with RGB noise to simulate grain or high ISO.
- **H.264 degradation:** approximates video artifacts using JPEG compression, resolution reduction, and resampling. It does not perform actual H.264 encoding.

The `seed` reproduces the license plates and randomized parameter values. However, noise pixels use random system data and may differ between runs.

## Character-Pair Cropping

The project also includes an optional tool that extracts consecutive character pairs from generated license plates. Perspective and rotation values are randomized separately for every pair:

```bash
python3 -m src.crop_plates
```

By default, it reads images from `generated-images/plates`, saves transformed crops to `generated-images/crop`, and writes matching metadata to `generated-images/crop-labels`:

```text
generated-images/
├── crop/
│   └── placa_RAG3E76_v01_pair_01_RA.jpg
└── crop-labels/
    └── placa_RAG3E76_v01_pair_01_RA.json
```

Each pair label records its position, text, camera elevation, horizontal perspective angle, and rotation. To see all available options, run:

```bash
python3 -m src.crop_plates --help
```

## Project Structure

```text
plate-detection/
├── data/inputs.json          # Generation settings
├── fonts/FE-Schrift.ttf      # Font used on the plates
├── main.py                   # Main generation pipeline
├── requirements.txt          # Python dependencies
├── src/config.py             # Plate dimensions and appearance
├── src/plate.py              # Plate rendering
├── src/plate_generator.py    # Random identifier generation
├── src/post_process.py       # Effects and degradation
└── src/crop_plates.py        # Optional character-pair extraction
```

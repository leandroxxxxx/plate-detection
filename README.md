# Synthetic License Plate Character Generator

This project generates synthetic images of character strings (1, 2, 3+ characters) rendered in the Mercosul license plate style and creates degraded variations that simulate security camera footage. It can be used to build datasets for OCR, character detection, and image-processing tests.

For each character string, the project:

1. generates a random identifier with N characters (configurable via `num_chars`);
2. renders the characters centered on a white background with the FE-Schrift font;
3. adds a gray border (default 30% of the smallest dimension);
4. creates multiple versions with randomized parameters;
5. applies 3D perspective (pitch, yaw, roll), motion blur, sharpening, noise, and simulated H.264 compression;
6. saves the image and a JSON label containing the applied parameters.

An optional second stage extracts consecutive character pairs (chunks) from each generated image for training detection models.

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
    "num_plates": 1300,
    "num_chars": 2,
    "versions_per_plate": 4,
    "seed": 42,
    "plate_border": {
        "size_percent": 30,
        "color": [128, 128, 128]
    },
    "effects": {
        "perspective_3d": {
            "pitch_range": [10, 45],
            "yaw_range": [-15, 15],
            "roll_range": [-5, 5],
            "focal_length_range": [0.8, 1.5]
        },
        "motion_blur": {
            "angle_range": [10, 20],
            "intensity_range": [0, 2]
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

- `num_plates`: number of different character strings to generate.
- `num_chars`: number of characters per string (1, 2, 3, etc.).
- `versions_per_plate`: number of variations generated for each string.
- `seed`: controls character generation and parameter randomization.
- `plate_border`: gray border added around the rendered plate (`size_percent` as percentage of the smallest dimension).
- `perspective_3d`: 3D perspective transformation parameters (pitch, yaw, roll, focal length). Each parameter is randomly sampled within its range.
- `motion_blur.angle_range`: motion blur angle range, in degrees.
- `motion_blur.intensity_range`: motion blur kernel size range.
- `sharpening.percent_range`: sharpening strength range.
- `noise.intensity_range`: noise intensity range (0.0 to 1.0).
- `h264.degradation_level_range`: compression degradation range.

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

## Generated Files

The output is separated into images and labels:

```text
generated-images/
├── plates/
│   ├── char2_AB_v01.jpg
│   ├── char2_AB_v02.jpg
│   ├── char2_AB_v03.jpg
│   └── char2_AB_v04.jpg
└── labels/
    ├── char2_AB_v01.json
    ├── char2_AB_v02.json
    ├── char2_AB_v03.json
    └── char2_AB_v04.json
```

Each image and its label share the same base filename. The naming format is `char{N}_{TEXT}_v{VERSION}.jpg`, where `N` is the number of characters. A label has the following structure:

```json
{
    "plate": "AB",
    "version": 1,
    "plate_border": {
        "size_percent": 30,
        "size_pixels": 10,
        "color": [128, 128, 128]
    },
    "perspective_3d": {
        "pitch": 32.38,
        "yaw": -14.25,
        "roll": -2.25,
        "focal_length": 0.96
    },
    "motion_blur": {
        "angle": 17.36,
        "intensity": 2
    },
    "sharpening": {
        "percent": 197
    },
    "noise": {
        "intensity": 0.0657
    },
    "h264": {
        "degradation_level": 81
    }
}
```

## Applied Effects

- **3D Perspective (pitch, yaw, roll):** simulates a license plate observed by a security camera from various angles, using a pinhole camera model with configurable focal length.
- **Motion blur:** overlays shifted copies of the image to simulate movement.
- **Sharpening:** enhances edges and creates halos similar to those produced by security cameras.
- **Noise:** blends the image with RGB noise to simulate grain or high ISO.
- **H.264 degradation:** approximates video artifacts using JPEG compression, resolution reduction, and resampling. It does not perform actual H.264 encoding.

The `seed` reproduces the character strings and randomized parameter values. However, noise pixels use random system data and may differ between runs.

## Character Chunk Cropping

The project also includes an optional tool that extracts consecutive character pairs (chunks) from generated images:

```bash
python3 -m src.crop_plates
```

By default, it reads images from `generated-images/plates`, saves crops to `generated-images/crop`, and writes matching metadata to `generated-images/crop-labels`:

```text
generated-images/
├── crop/
│   └── crop_char2_AB_v01_01.jpg
└── crop-labels/
    └── crop_char2_AB_v01_01.json
```

Each crop label records its source image, text, chunk content, index, and bounding box:

```json
{
    "source_image": "char2_AB_v01.jpg",
    "plate": "AB",
    "chunk": "AB",
    "chunk_index": 1,
    "crop_box": {
        "x": 55,
        "y": 60,
        "width": 60,
        "height": 60
    }
}
```

To see all available options, run:

```bash
python3 -m src.crop_plates --help
```

## Project Structure

```text
plate-detection/
├── data/inputs.json              # Generation settings
├── fonts/FE-Schrift.ttf          # Font used on the plates
├── main.py                       # Main generation pipeline
├── requirements.txt              # Python dependencies
├── src/config.py                 # Plate dimensions and appearance
├── src/plate.py                  # Plate rendering
├── src/plate_generator.py        # Random character string generation
├── src/post_process.py           # Effects and degradation
└── src/crop_plates.py            # Optional character chunk extraction
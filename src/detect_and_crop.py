import cv2
import numpy as np
import os
import glob
import json

"""
Detects 2 alphanumeric characters in a 60x60 image (white background + noise)
and crops a fixed-size region (e.g. 30x30) centered on the characters.

Strategy:
1. Binarize the image (dark pixel = content).
2. Find connected components (blobs).
3. Discard very small blobs (noise) based on area.
4. Compute the bounding box of the union of remaining blobs (the 2 characters).
5. Crop a square of the desired size centered on that bounding box,
   clamping to stay within image boundaries.
6. Validate the crop: if it's almost all white, the detection failed and
   the file is removed to avoid polluting the dataset.
"""

def detect_and_crop(
    image_path: str,
    output_size: int = 30,
    binarization_threshold: int = 200,
    min_blob_area: int = 8,
    output_path: str | None = None,
    debug: bool = False,
):
    """
    Parameters
    ----------
    image_path : str
        Path to the input image (60x60, white background).
    output_size : int
        Size of the final crop (e.g. 30 -> 30x30 crop).
    binarization_threshold : int
        Threshold (0-255). Pixels with value < threshold are considered "dark"/content.
        Adjust according to your image contrast.
    min_blob_area : int
        Minimum area (in pixels) for a connected component to be considered
        part of a character rather than noise. Adjust according to noise size.
    output_path : str | None
        If provided, saves the crop to this path.
    debug : bool
        If True, prints intermediate info (bbox, discarded blobs, etc.).

    Returns
    -------
    crop : np.ndarray
        Cropped image (output_size x output_size), grayscale.
    """
    # 1. Load as grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not open: {image_path}")

    h, w = img.shape

    # 2. Binarize: white background -> 0 (background), dark content -> 255 (foreground)
    _, binary = cv2.threshold(img, binarization_threshold, 255, cv2.THRESH_BINARY_INV)

    # 3. Connected components (8-connectivity)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary, connectivity=8
    )
    # stats[i] = [x, y, width, height, area]; label 0 is always the background

    valid_blobs = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_blob_area:
            valid_blobs.append(i)
        elif debug:
            print(f"Blob {i} discarded as noise (area={area})")

    if not valid_blobs:
        raise ValueError(
            "No significant blobs found. "
            "Try lowering 'min_blob_area' or adjusting 'binarization_threshold'."
        )

    # 4. Bounding box of the union of valid blobs (the characters)
    x_min = min(stats[i, cv2.CC_STAT_LEFT] for i in valid_blobs)
    y_min = min(stats[i, cv2.CC_STAT_TOP] for i in valid_blobs)
    x_max = max(
        stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] for i in valid_blobs
    )
    y_max = max(
        stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] for i in valid_blobs
    )

    center_x = (x_min + x_max) // 2
    center_y = (y_min + y_max) // 2

    if debug:
        print(f"Character bbox: x=({x_min},{x_max}) y=({y_min},{y_max})")
        print(f"Calculated center: ({center_x}, {center_y})")

    # 5. Compute the centered crop window, clamping to image boundaries
    half = output_size // 2

    x_start = center_x - half
    y_start = center_y - half
    x_end = x_start + output_size
    y_end = y_start + output_size

    # Horizontal clamping
    if x_start < 0:
        x_end -= x_start
        x_start = 0
    if x_end > w:
        x_start -= (x_end - w)
        x_end = w
        x_start = max(x_start, 0)

    # Vertical clamping
    if y_start < 0:
        y_end -= y_start
        y_start = 0
    if y_end > h:
        y_start -= (y_end - h)
        y_end = h
        y_start = max(y_start, 0)

    crop = img[y_start:y_end, x_start:x_end]

    # Ensure exact output size (if the original image is smaller than
    # output_size in any axis, pad with white)
    if crop.shape != (output_size, output_size):
        final_crop = np.full((output_size, output_size), 255, dtype=np.uint8)
        rh, rw = crop.shape
        final_crop[:rh, :rw] = crop
        crop = final_crop

    if output_path:
        cv2.imwrite(output_path, crop)

    return crop


def validate_crop(
    crop: np.ndarray,
    max_white_pixels_percent: float = 95.0,
    min_character_area_percent: float = 1.0,
) -> bool:
    """
    Validates that the crop has minimum content (not an almost all-white image).

    Parameters
    ----------
    crop : np.ndarray
        Cropped grayscale image.
    max_white_pixels_percent : float
        Maximum percentage of white pixels (>240) allowed.
        Above this, detection is considered to have failed.
    min_character_area_percent : float
        Minimum percentage of dark pixels (<=240) relative to total.
        Below this, there is considered to be no character.

    Returns
    -------
    bool
        True if the crop passes validation, False if it should be discarded.
    """
    total_pixels = crop.size
    if total_pixels == 0:
        return False

    # Count white pixels (close to 255)
    white_pixels = np.sum(crop > 240)
    white_percent = (white_pixels / total_pixels) * 100.0

    # Count dark pixels (content)
    dark_pixels = np.sum(crop <= 240)
    dark_percent = (dark_pixels / total_pixels) * 100.0

    # If there are too many white pixels, the detection probably caught nothing
    if white_percent > max_white_pixels_percent:
        return False

    # If there is very little dark content, it is also suspicious
    if dark_percent < min_character_area_percent:
        return False

    return True


def process_folder(
    config: dict,
    debug: bool = False,
):
    """
    Processes all images in the input folder by applying
    detect_and_crop, validating, and saving to the output folder.

    Parameters
    ----------
    config : dict
        Dictionary with detect_and_crop settings from inputs.json.
    debug : bool
        If True, displays detailed information.
    """
    input_dir = config.get("input_dir", "generated-images/crop")
    output_dir = config.get("output_dir", "generated-images/detected")
    output_size = config.get("output_size", 30)
    binarization_threshold = config.get("binarization_threshold", 200)
    min_blob_area = config.get("min_blob_area", 8)

    # Validation settings
    validation_cfg = config.get("validation", {})
    validation_enabled = validation_cfg.get("enabled", True)
    max_white_pixels_percent = validation_cfg.get("max_white_pixels_percent", 95)
    min_character_area_percent = validation_cfg.get("min_character_area_percent", 1.0)

    os.makedirs(output_dir, exist_ok=True)

    # Find .jpg and .png images
    patterns = ["*.jpg", "*.jpeg", "*.png"]
    files = []
    for pattern in patterns:
        files.extend(sorted(glob.glob(os.path.join(input_dir, pattern))))

    if not files:
        print(f"No images found in: {input_dir}")
        return

    total = len(files)
    errors = 0
    removed = 0

    print(f"Processing {total} image(s)...")
    print(f"  Input:  {input_dir}")
    print(f"  Output: {output_dir}")
    print(f"  Crop size: {output_size}x{output_size}")
    print(f"  Validation: {'Enabled' if validation_enabled else 'Disabled'}")
    if validation_enabled:
        print(f"    Max white pixels: {max_white_pixels_percent}%")
        print(f"    Min character area: {min_character_area_percent}%")
    print()

    for i, path in enumerate(files, start=1):
        filename = os.path.basename(path)
        output_path = os.path.join(output_dir, filename)

        try:
            crop = detect_and_crop(
                image_path=path,
                output_size=output_size,
                binarization_threshold=binarization_threshold,
                min_blob_area=min_blob_area,
                output_path=None,  # save manually after validation
                debug=False,
            )

            # Validate the crop before saving
            if validation_enabled:
                if not validate_crop(
                    crop,
                    max_white_pixels_percent=max_white_pixels_percent,
                    min_character_area_percent=min_character_area_percent,
                ):
                    removed += 1
                    if debug:
                        print(f"  [REMOVED] [{i}/{total}] {filename} -> validation failed")
                    continue  # don't save

            # Save only if it passed validation
            cv2.imwrite(output_path, crop)

            if debug or i % 1000 == 0:
                print(f"  [{i}/{total}] {filename} -> OK")

        except Exception as e:
            errors += 1
            removed += 1
            if debug:
                print(f"  [ERROR] [{i}/{total}] {filename}: {e}")

    print()
    print(f"Done!")
    print(f"  Total images processed: {total}")
    print(f"  Crops saved: {total - errors - removed}")
    print(f"  Removed (validation/error): {removed}")
    print(f"  Errors: {errors}")
    print(f"  Crops saved in: {output_dir}")


def main():
    # Load configuration from inputs.json
    config_path = os.path.join("data", "inputs.json")
    if not os.path.exists(config_path):
        # Try alternate path if running from another directory
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "inputs.json"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        inputs = json.load(f)

    detect_cfg = inputs.get("detect_and_crop", {})
    if not detect_cfg.get("enabled", True):
        print("detect_and_crop is disabled in inputs.json.")
        return

    process_folder(detect_cfg)


if __name__ == "__main__":
    main()
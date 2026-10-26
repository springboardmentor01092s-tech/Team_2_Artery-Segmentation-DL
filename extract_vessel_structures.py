import os
import cv2
import numpy as np
from skimage.morphology import skeletonize


# ==========================================
# SETTINGS
# ==========================================

DATASETS = ["syntax", "stenosis"]

BASE_PATH = "dataset/arcade"

print("Vessel structure extraction started...")
# ==========================================
# PROCESS BOTH DATASETS
# ==========================================

for dataset in DATASETS:

    INPUT_DIR = os.path.join(
        BASE_PATH,
        dataset,
        "test",
        "processed_masks"
    )

    OUTPUT_DIR = os.path.join(
        BASE_PATH,
        dataset,
        "test",
        "vessel_structures"
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    print("\nDataset:", dataset.upper())
    print("Input:", INPUT_DIR)
    print("Output:", OUTPUT_DIR)
        # ==========================================
    # EXTRACT VESSEL STRUCTURE
    # ==========================================

    mask_files = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith(".png")
    ]

    mask_files.sort()

    print("Masks found:", len(mask_files))

    for filename in mask_files:

        input_path = os.path.join(
            INPUT_DIR,
            filename
        )

        output_path = os.path.join(
            OUTPUT_DIR,
            filename
        )

        # Read processed mask
        mask = cv2.imread(
            input_path,
            cv2.IMREAD_GRAYSCALE
        )

        if mask is None:
            print("Could not read:", filename)
            continue

        # Convert to binary
        binary = mask > 127

        # Skeletonize the vessel mask
        skeleton = skeletonize(binary)

        # Convert True/False to 0/255
        skeleton = (
            skeleton.astype(np.uint8) * 255
        )

        # Save vessel structure
        cv2.imwrite(
            output_path,
            skeleton
        )

    print(
        "Vessel structures saved:",
        OUTPUT_DIR
    )


print("\n================================")
print("VESSEL STRUCTURE EXTRACTION DONE")
print("================================")
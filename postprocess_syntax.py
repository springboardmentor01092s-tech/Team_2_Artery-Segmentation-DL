# ==========================================
# POST-PROCESSING
# ==========================================
import os
import cv2
import numpy as np

# ==========================================
# PATHS
# ==========================================

INPUT_MASK_DIR = "dataset/arcade/syntax/test/predicted_masks"

OUTPUT_MASK_DIR = "dataset/arcade/syntax/test/processed_masks"

os.makedirs(OUTPUT_MASK_DIR, exist_ok=True)

print("Syntax post-processing started...")
mask_files = [
    f for f in os.listdir(INPUT_MASK_DIR)
    if f.lower().endswith(".png")
]

mask_files.sort()

print("Predicted masks:", len(mask_files))


for filename in mask_files:

    input_path = os.path.join(
        INPUT_MASK_DIR,
        filename
    )

    output_path = os.path.join(
        OUTPUT_MASK_DIR,
        filename
    )

    mask = cv2.imread(
        input_path,
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:
        continue

    # Binary mask
    _, binary = cv2.threshold(
        mask,
        127,
        255,
        cv2.THRESH_BINARY
    )

    # Remove small isolated noise
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary,
        connectivity=8
    )

    cleaned = np.zeros_like(binary)

    for i in range(1, num_labels):

        area = stats[i, cv2.CC_STAT_AREA]

        if area >= 50:
            cleaned[labels == i] = 255

    # Morphological closing to connect small gaps
    kernel = np.ones((3, 3), np.uint8)

    cleaned = cv2.morphologyEx(
        cleaned,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    # Small opening to remove remaining noise
    cleaned = cv2.morphologyEx(
        cleaned,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    cv2.imwrite(
        output_path,
        cleaned
    )


print("\n================================")
print("POST-PROCESSING COMPLETED")
print("================================")
print(
    "Processed masks saved in:",
    OUTPUT_MASK_DIR
)
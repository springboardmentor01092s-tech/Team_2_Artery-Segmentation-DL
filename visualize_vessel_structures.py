import os
import cv2
import matplotlib.pyplot as plt

# ==========================================
# PATHS
# ==========================================

IMAGE_DIR = "dataset/arcade/syntax/test/images"

MASK_DIR = "dataset/arcade/syntax/test/processed_masks"

VESSEL_DIR = "dataset/arcade/syntax/test/vessel_structures"


# ==========================================
# SELECT IMAGE
# ==========================================

files = [
    f for f in os.listdir(IMAGE_DIR)
    if f.lower().endswith(".png")
]

files.sort()

filename = files[0]

print("Visualizing:", filename)


# ==========================================
# LOAD IMAGES
# ==========================================

original = cv2.imread(
    os.path.join(IMAGE_DIR, filename)
)

original = cv2.cvtColor(
    original,
    cv2.COLOR_BGR2RGB
)

processed = cv2.imread(
    os.path.join(MASK_DIR, filename),
    cv2.IMREAD_GRAYSCALE
)

vessel = cv2.imread(
    os.path.join(VESSEL_DIR, filename),
    cv2.IMREAD_GRAYSCALE
)


# ==========================================
# DISPLAY
# ==========================================

plt.figure(figsize=(15, 5))


plt.subplot(1, 3, 1)

plt.imshow(original)

plt.title("Original Image")

plt.axis("off")


plt.subplot(1, 3, 2)

plt.imshow(
    processed,
    cmap="gray"
)

plt.title("Post-Processed")

plt.axis("off")


plt.subplot(1, 3, 3)

plt.imshow(
    vessel,
    cmap="gray"
)

plt.title("Extracted Vessel Structure")

plt.axis("off")


plt.tight_layout()

plt.show()
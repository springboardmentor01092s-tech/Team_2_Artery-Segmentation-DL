import cv2
import matplotlib.pyplot as plt
import os

# ==============================
# SYNTAX MASK CHECK
# ==============================

image_path = "dataset/arcade/stenosis/train/images/922.png"
mask_path = "dataset/arcade/stenosis/train/masks/922.png"

image = cv2.imread(image_path)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title("Original Stenosis Image")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(mask, cmap="gray")
plt.title("Stenosis Mask")
plt.axis("off")

plt.tight_layout()
plt.show()
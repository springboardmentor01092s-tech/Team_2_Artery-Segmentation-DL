import os
import cv2
import matplotlib.pyplot as plt

IMAGE_DIR = "dataset/arcade/syntax/test/images"
GROUND_TRUTH_DIR = "dataset/arcade/syntax/test/masks"
PREDICTED_DIR = "dataset/arcade/syntax/test/predicted_masks"
PROCESSED_DIR = "dataset/arcade/syntax/test/processed_masks"

filename = sorted([
    f for f in os.listdir(IMAGE_DIR)
    if f.lower().endswith(".png")
])[0]

image = cv2.imread(
    os.path.join(IMAGE_DIR, filename)
)

image = cv2.cvtColor(
    image,
    cv2.COLOR_BGR2RGB
)

ground_truth = cv2.imread(
    os.path.join(GROUND_TRUTH_DIR, filename),
    cv2.IMREAD_GRAYSCALE
)

predicted = cv2.imread(
    os.path.join(PREDICTED_DIR, filename),
    cv2.IMREAD_GRAYSCALE
)

processed = cv2.imread(
    os.path.join(PROCESSED_DIR, filename),
    cv2.IMREAD_GRAYSCALE
)

plt.figure(figsize=(16, 4))

plt.subplot(1, 4, 1)
plt.imshow(image)
plt.title("Original Image")
plt.axis("off")

plt.subplot(1, 4, 2)
plt.imshow(ground_truth, cmap="gray")
plt.title("Ground Truth")
plt.axis("off")

plt.subplot(1, 4, 3)
plt.imshow(predicted, cmap="gray")
plt.title("U-Net Prediction")
plt.axis("off")

plt.subplot(1, 4, 4)
plt.imshow(processed, cmap="gray")
plt.title("Post-Processed")
plt.axis("off")

plt.tight_layout()
plt.show()
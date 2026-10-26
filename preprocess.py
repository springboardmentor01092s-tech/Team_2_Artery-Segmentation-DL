import os
import cv2

# ==============================
# PATHS
# ==============================

base_path = "dataset/arcade"

datasets = ["syntax", "stenosis"]
splits = ["train", "val", "test"]


# ==============================
# PREPROCESS IMAGES
# ==============================

for dataset in datasets:

    print("\n==============================")
    print("PREPROCESSING:", dataset.upper())
    print("==============================")

    for split in splits:

        input_path = os.path.join(
            base_path, dataset, split, "images"
        )

        output_path = os.path.join(
            base_path,
            dataset,
            split,
            "preprocessed_images"
        )

        # Create output folder
        os.makedirs(output_path, exist_ok=True)

        if not os.path.exists(input_path):
            print(split, ": images folder not found")
            continue

        image_files = [
            f for f in os.listdir(input_path)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        processed = 0
        failed = 0

        for file in image_files:

            input_file = os.path.join(input_path, file)
            output_file = os.path.join(output_path, file)

            # Read image
            image = cv2.imread(input_file)

            if image is None:
                failed += 1
                continue

            # Convert pixel values from 0-255 to 0-1
            image_normalized = image.astype("float32") / 255.0

            # Convert back to 0-255 for saving
            image_processed = (image_normalized * 255).astype("uint8")

            # Save processed image
            cv2.imwrite(output_file, image_processed)

            processed += 1

        print(f"{split}: {processed} images processed")
        print(f"{split}: {failed} images failed")

print("\n==============================")
print("PREPROCESSING COMPLETED")
print("==============================")
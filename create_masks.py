import os
import json
import cv2
import numpy as np

BASE_PATH = "dataset/arcade"

DATASETS = ["syntax", "stenosis"]
SPLITS = ["train", "val", "test"]


def create_masks(dataset, split):

    annotation_file = os.path.join(
        BASE_PATH,
        dataset,
        split,
        "annotations",
        f"{split}.json"
    )

    image_folder = os.path.join(
        BASE_PATH,
        dataset,
        split,
        "images"
    )

    mask_folder = os.path.join(
        BASE_PATH,
        dataset,
        split,
        "masks"
    )

    os.makedirs(mask_folder, exist_ok=True)

    # Read annotation JSON
    with open(annotation_file, "r") as f:
        data = json.load(f)

    # Create mapping: image ID → image information
    image_map = {
        image["id"]: image
        for image in data["images"]
    }

    # Group annotations by image
    annotations_by_image = {}

    for ann in data["annotations"]:

        image_id = ann["image_id"]

        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []

        annotations_by_image[image_id].append(ann)

    processed = 0

    # Process every image
    for image_id, image_info in image_map.items():

        file_name = image_info["file_name"]

        image_path = os.path.join(
            image_folder,
            file_name
        )

        image = cv2.imread(image_path)

        if image is None:
            print("Could not read:", image_path)
            continue

        height, width = image.shape[:2]

        # Create black mask
        mask = np.zeros(
            (height, width),
            dtype=np.uint8
        )

        # Get annotations for this image
        annotations = annotations_by_image.get(
            image_id, []
        )

        for ann in annotations:

            segmentation = ann.get("segmentation", [])

            if not segmentation:
                continue

            # Draw each polygon
            for polygon in segmentation:

                points = np.array(
                    polygon,
                    dtype=np.float32
                ).reshape(-1, 2)

                points = np.round(points).astype(
                    np.int32
                )

                cv2.fillPoly(
                    mask,
                    [points],
                    255
                )

        # Save mask
        mask_name = os.path.splitext(
            file_name
        )[0] + ".png"

        mask_path = os.path.join(
            mask_folder,
            mask_name
        )

        cv2.imwrite(mask_path, mask)

        processed += 1

    print(
        f"{dataset.upper()} {split}: "
        f"{processed} masks created"
    )


# ==================================
# RUN FOR BOTH DATASETS
# ==================================

for dataset in DATASETS:

    for split in SPLITS:

        create_masks(
            dataset,
            split
        )

print("\n==============================")
print("MASK CREATION COMPLETED")
print("==============================")
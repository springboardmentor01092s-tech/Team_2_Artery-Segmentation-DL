import os
import json
import shutil

base_path = "dataset/arcade"

datasets = ["syntax", "stenosis"]
splits = ["train", "val", "test"]

for dataset in datasets:

    print("\n==============================")
    print("PREPARING:", dataset.upper())
    print("==============================")

    for split in splits:

        annotation_path = os.path.join(
            base_path,
            dataset,
            split,
            "annotations",
            f"{split}.json"
        )

        output_folder = os.path.join(
            base_path,
            dataset,
            split,
            "prepared_annotations"
        )

        os.makedirs(output_folder, exist_ok=True)

        if not os.path.exists(annotation_path):
            print(split, ": annotation file not found")
            continue

        # Read JSON
        with open(annotation_path, "r") as f:
            data = json.load(f)

        # Basic validation
        print(f"\n{split.upper()}")
        print("Images:", len(data["images"]))
        print("Annotations:", len(data["annotations"]))
        print("Categories:", len(data["categories"]))

        # Save prepared copy
        output_path = os.path.join(
            output_folder,
            f"{split}.json"
        )

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print("Saved:", output_path)

print("\n==============================")
print("ANNOTATION PREPARATION COMPLETED")
print("==============================")
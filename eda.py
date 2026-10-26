import os
from PIL import Image
from collections import Counter

base_path = "dataset/arcade"

datasets = ["syntax", "stenosis"]
splits = ["train", "val", "test"]

for dataset in datasets:

    print("\n==============================")
    print(dataset.upper())
    print("==============================")

    all_dimensions = []
    all_formats = Counter()
    total_images = 0

    for split in splits:

        image_path = os.path.join(
            base_path, dataset, split, "images"
        )

        if not os.path.exists(image_path):
            print(f"{split}: images folder not found")
            continue

        image_files = [
            f for f in os.listdir(image_path)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        for file in image_files:

            file_path = os.path.join(image_path, file)

            try:
                with Image.open(file_path) as img:

                    # Image dimensions
                    all_dimensions.append(img.size)

                    # Image format
                    all_formats[img.format] += 1

                    total_images += 1

            except Exception as e:
                print("Error reading:", file, e)

    print("Total images:", total_images)

    print("\nImage formats:")
    for fmt, count in all_formats.items():
        print(fmt, ":", count)

    print("\nMost common dimensions:")
    dimension_counts = Counter(all_dimensions)

    for dimension, count in dimension_counts.most_common(10):
        print(dimension, ":", count)
        
import json

# -----------------------------
# Check SYNTAX annotations
# -----------------------------

path = "dataset/arcade/syntax/train/annotations/train.json"

with open(path, "r") as f:
    data = json.load(f)

print("\n==============================")
print("SYNTAX ANNOTATION EDA")
print("==============================")

print("Keys:", data.keys())

print("Number of images:", len(data["images"]))
print("Number of annotations:", len(data["annotations"]))
print("Number of categories:", len(data["categories"]))

print("\nCategories:")
for category in data["categories"]:
    print(category)
    
import json

# -----------------------------
# Check STENOSIS annotations
# -----------------------------

path = "dataset/arcade/stenosis/train/annotations/train.json"

with open(path, "r") as f:
    data = json.load(f)

print("\n==============================")
print("STENOSIS ANNOTATION EDA")
print("==============================")

print("Keys:", data.keys())

print("Number of images:", len(data["images"]))
print("Number of annotations:", len(data["annotations"]))
print("Number of categories:", len(data["categories"]))

print("\nCategories:")
for category in data["categories"]:
    print(category)

import json

# ==============================
# SYNTAX CATEGORIES
# ==============================

syntax_path = "dataset/arcade/syntax/train/annotations/train.json"

with open(syntax_path, "r") as f:
    syntax_data = json.load(f)

print("\n==============================")
print("SYNTAX CATEGORIES")
print("==============================")

for category in syntax_data["categories"]:
    print("ID:", category["id"], "| Name:", category["name"])


# ==============================
# STENOSIS CATEGORIES
# ==============================

stenosis_path = "dataset/arcade/stenosis/train/annotations/train.json"

with open(stenosis_path, "r") as f:
    stenosis_data = json.load(f)

print("\n==============================")
print("STENOSIS CATEGORIES")
print("==============================")

for category in stenosis_data["categories"]:
    print("ID:", category["id"], "| Name:", category["name"])
from collections import Counter

# ==============================
# SYNTAX ANNOTATION DISTRIBUTION
# ==============================

syntax_counts = Counter(
    ann["category_id"] for ann in syntax_data["annotations"]
)

print("\n==============================")
print("SYNTAX ANNOTATION DISTRIBUTION")
print("==============================")

for category in syntax_data["categories"]:
    cid = category["id"]
    name = category["name"]
    print(name, ":", syntax_counts[cid])


# ==============================
# STENOSIS ANNOTATION DISTRIBUTION
# ==============================

stenosis_counts = Counter(
    ann["category_id"] for ann in stenosis_data["annotations"]
)

print("\n==============================")
print("STENOSIS ANNOTATION DISTRIBUTION")
print("==============================")

for category in stenosis_data["categories"]:
    cid = category["id"]
    name = category["name"]
    print(name, ":", stenosis_counts[cid])
    
# ==============================
# ANNOTATION STRUCTURE
# ==============================

print("\n==============================")
print("SYNTAX ANNOTATION STRUCTURE")
print("==============================")

sample = syntax_data["annotations"][0]

print("Annotation keys:")
print(sample.keys())

print("\nSample annotation:")
print(sample)


print("\n==============================")
print("STENOSIS ANNOTATION STRUCTURE")
print("==============================")

sample = stenosis_data["annotations"][0]

print("Annotation keys:")
print(sample.keys())

print("\nSample annotation:")
print(sample)

# ==============================
# IMAGE-ANNOTATION MATCHING
# ==============================

def check_matching(data, name):

    image_ids = set(img["id"] for img in data["images"])
    annotation_image_ids = set(
        ann["image_id"] for ann in data["annotations"]
    )

    matched = image_ids & annotation_image_ids
    missing = annotation_image_ids - image_ids

    print("\n==============================")
    print(name, "IMAGE-ANNOTATION CHECK")
    print("==============================")

    print("Total images:", len(image_ids))
    print("Images having annotations:", len(matched))
    print("Annotation image IDs without matching image:", len(missing))

    if missing:
        print("Missing IDs:", list(missing)[:10])
    else:
        print("All annotation image IDs have matching images.")


check_matching(syntax_data, "SYNTAX")
check_matching(stenosis_data, "STENOSIS")
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os

# ==================================================
# SYNTAX VISUALIZATION
# ==================================================

syntax_image_info = syntax_data["images"][0]

syntax_image_path = os.path.join(
    "dataset/arcade/syntax/train/images",
    syntax_image_info["file_name"]
)

print("\nSYNTAX IMAGE:")
print(syntax_image_path)

syntax_image = cv2.imread(syntax_image_path)
syntax_image = cv2.cvtColor(syntax_image, cv2.COLOR_BGR2RGB)

plt.figure(figsize=(8, 8))
plt.imshow(syntax_image)

for ann in syntax_data["annotations"]:

    if ann["image_id"] == syntax_image_info["id"]:

        for polygon in ann["segmentation"]:

            points = np.array(polygon).reshape(-1, 2)

            plt.plot(
                points[:, 0],
                points[:, 1],
                linewidth=2
            )

plt.title("ARCADE Syntax - Sample Annotation")
plt.axis("off")
plt.savefig("syntax_sample.png")
plt.close()


# ==================================================
# STENOSIS VISUALIZATION
# ==================================================

# Find an image that HAS a stenosis annotation

stenosis_annotated_ids = set(
    ann["image_id"]
    for ann in stenosis_data["annotations"]
)

stenosis_image_info = next(
    img for img in stenosis_data["images"]
    if img["id"] in stenosis_annotated_ids
)

stenosis_image_path = os.path.join(
    "dataset/arcade/stenosis/train/images",
    stenosis_image_info["file_name"]
)

print("\nSTENOSIS IMAGE:")
print(stenosis_image_path)

stenosis_image = cv2.imread(stenosis_image_path)

if stenosis_image is None:
    print("ERROR: Stenosis image not found!")

else:

    stenosis_image = cv2.cvtColor(
        stenosis_image,
        cv2.COLOR_BGR2RGB
    )

    plt.figure(figsize=(8, 8))
    plt.imshow(stenosis_image)

    for ann in stenosis_data["annotations"]:

        if ann["image_id"] == stenosis_image_info["id"]:

            for polygon in ann["segmentation"]:

                points = np.array(
                    polygon
                ).reshape(-1, 2)

                plt.plot(
                    points[:, 0],
                    points[:, 1],
                    linewidth=2
                )

    plt.title("ARCADE Stenosis - Sample Annotation")
    plt.axis("off")
    plt.show()
# ==============================
# ANNOTATION SIZE ANALYSIS
# ==============================

print("\n==============================")
print("ANNOTATION SIZE ANALYSIS")
print("==============================")

# SYNTAX
syntax_areas = [
    ann["area"]
    for ann in syntax_data["annotations"]
    if ann["area"] > 0
]

# STENOSIS
stenosis_areas = [
    ann["area"]
    for ann in stenosis_data["annotations"]
    if ann["area"] > 0
]

print("\nSYNTAX")
print("Minimum annotation area:", min(syntax_areas))
print("Maximum annotation area:", max(syntax_areas))
print("Average annotation area:", sum(syntax_areas) / len(syntax_areas))

print("\nSTENOSIS")
print("Minimum annotation area:", min(stenosis_areas))
print("Maximum annotation area:", max(stenosis_areas))
print("Average annotation area:", sum(stenosis_areas) / len(stenosis_areas))

# ==============================
# IMAGE INTENSITY ANALYSIS
# ==============================

from PIL import Image
import numpy as np

print("\n==============================")
print("IMAGE INTENSITY ANALYSIS")
print("==============================")

for dataset in ["syntax", "stenosis"]:

    image_path = os.path.join(
        base_path, dataset, "train", "images"
    )

    image_files = [
        f for f in os.listdir(image_path)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    means = []

    for file in image_files:

        path = os.path.join(image_path, file)

        img = Image.open(path).convert("L")

        arr = np.array(img)

        means.append(arr.mean())

    print("\n", dataset.upper())

    print("Minimum mean intensity:", min(means))
    print("Maximum mean intensity:", max(means))
    print("Average mean intensity:", sum(means) / len(means))
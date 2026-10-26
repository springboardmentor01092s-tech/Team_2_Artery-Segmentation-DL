import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


# ==========================================
# 1. SETTINGS
# ==========================================

IMAGE_SIZE = 256
BATCH_SIZE = 8

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", DEVICE)


# ==========================================
# 2. DATASET
# ==========================================

class ArteryDataset(Dataset):

    def __init__(self, image_dir, mask_dir):

        self.image_dir = image_dir
        self.mask_dir = mask_dir

        self.images = [
            f for f in os.listdir(image_dir)
            if f.lower().endswith(".png")
        ]

        self.images.sort()


    def __len__(self):
        return len(self.images)


    def __getitem__(self, index):

        image_name = self.images[index]

        image_path = os.path.join(
            self.image_dir,
            image_name
        )

        mask_path = os.path.join(
            self.mask_dir,
            image_name
        )

        # Read image
        image = cv2.imread(image_path)

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        # Read ground-truth mask
        mask = cv2.imread(
            mask_path,
            cv2.IMREAD_GRAYSCALE
        )

        # Resize
        image = cv2.resize(
            image,
            (IMAGE_SIZE, IMAGE_SIZE)
        )

        mask = cv2.resize(
            mask,
            (IMAGE_SIZE, IMAGE_SIZE),
            interpolation=cv2.INTER_NEAREST
        )

        # Normalize image
        image = image.astype(np.float32) / 255.0

        # Convert mask to 0/1
        mask = (mask > 0).astype(np.float32)

        # HWC → CHW
        image = np.transpose(
            image,
            (2, 0, 1)
        )

        image = torch.tensor(
            image,
            dtype=torch.float32
        )

        mask = torch.tensor(
            mask,
            dtype=torch.float32
        ).unsqueeze(0)

        return image, mask


# ==========================================
# 3. U-NET
# ==========================================

class DoubleConv(nn.Module):

    def __init__(self, in_channels, out_channels):

        super().__init__()

        self.block = nn.Sequential(

            nn.Conv2d(
                in_channels,
                out_channels,
                3,
                padding=1
            ),

            nn.BatchNorm2d(out_channels),

            nn.ReLU(inplace=True),

            nn.Conv2d(
                out_channels,
                out_channels,
                3,
                padding=1
            ),

            nn.BatchNorm2d(out_channels),

            nn.ReLU(inplace=True)
        )


    def forward(self, x):

        return self.block(x)


class UNet(nn.Module):

    def __init__(self):

        super().__init__()

        # Encoder
        self.conv1 = DoubleConv(3, 32)
        self.conv2 = DoubleConv(32, 64)
        self.conv3 = DoubleConv(64, 128)
        self.conv4 = DoubleConv(128, 256)

        self.pool = nn.MaxPool2d(2)

        # Bottleneck
        self.bottleneck = DoubleConv(
            256,
            512
        )

        # Decoder
        self.up4 = nn.ConvTranspose2d(
            512,
            256,
            2,
            stride=2
        )

        self.dec4 = DoubleConv(
            512,
            256
        )

        self.up3 = nn.ConvTranspose2d(
            256,
            128,
            2,
            stride=2
        )

        self.dec3 = DoubleConv(
            256,
            128
        )

        self.up2 = nn.ConvTranspose2d(
            128,
            64,
            2,
            stride=2
        )

        self.dec2 = DoubleConv(
            128,
            64
        )

        self.up1 = nn.ConvTranspose2d(
            64,
            32,
            2,
            stride=2
        )

        self.dec1 = DoubleConv(
            64,
            32
        )

        self.final = nn.Conv2d(
            32,
            1,
            1
        )


    def forward(self, x):

        # Encoder
        c1 = self.conv1(x)
        p1 = self.pool(c1)

        c2 = self.conv2(p1)
        p2 = self.pool(c2)

        c3 = self.conv3(p2)
        p3 = self.pool(c3)

        c4 = self.conv4(p3)
        p4 = self.pool(c4)

        # Bottleneck
        b = self.bottleneck(p4)

        # Decoder
        u4 = self.up4(b)
        u4 = torch.cat([u4, c4], dim=1)
        d4 = self.dec4(u4)

        u3 = self.up3(d4)
        u3 = torch.cat([u3, c3], dim=1)
        d3 = self.dec3(u3)

        u2 = self.up2(d3)
        u2 = torch.cat([u2, c2], dim=1)
        d2 = self.dec2(u2)

        u1 = self.up1(d2)
        u1 = torch.cat([u1, c1], dim=1)
        d1 = self.dec1(u1)

        return self.final(d1)


# ==========================================
# 4. LOAD TEST DATA
# ==========================================

test_dataset = ArteryDataset(
    "dataset/arcade/syntax/test/images",
    "dataset/arcade/syntax/test/masks"
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

print("Test images:", len(test_dataset))


# ==========================================
# 5. LOAD TRAINED MODEL
# ==========================================

model = UNet().to(DEVICE)

model.load_state_dict(
    torch.load(
        "models/unet_syntax.pth",
        map_location=DEVICE
    )
)

model.eval()

print("Syntax U-Net loaded successfully!")

# ==========================================
# 6. EVALUATE POST-PROCESSED MASKS
# ==========================================

PROCESSED_DIR = "dataset/arcade/syntax/test/processed_masks"

total_dice = 0
total_iou = 0
total_precision = 0
total_recall = 0

num_images = 0

EPS = 1e-7


for image_name in test_dataset.images:

    # Ground truth
    ground_truth_path = os.path.join(
        "dataset/arcade/syntax/test/masks",
        image_name
    )

    # Post-processed prediction
    processed_path = os.path.join(
        PROCESSED_DIR,
        image_name
    )

    target = cv2.imread(
        ground_truth_path,
        cv2.IMREAD_GRAYSCALE
    )

    pred = cv2.imread(
        processed_path,
        cv2.IMREAD_GRAYSCALE
    )

    if target is None or pred is None:
        print("Skipping:", image_name)
        continue

    # Resize ground truth to match prediction
    target = cv2.resize(
        target,
        (IMAGE_SIZE, IMAGE_SIZE),
        interpolation=cv2.INTER_NEAREST
    )

    # Convert to binary
    target = (
        target > 0
    ).astype(np.float32)

    pred = (
        pred > 127
    ).astype(np.float32)

    # Flatten
    pred = pred.flatten()
    target = target.flatten()

    # Intersection
    intersection = np.sum(
        pred * target
    )

    pred_sum = np.sum(pred)
    target_sum = np.sum(target)

    # Dice
    dice = (
        2 * intersection + EPS
    ) / (
        pred_sum + target_sum + EPS
    )

    # IoU
    union = (
        pred_sum +
        target_sum -
        intersection
    )

    iou = (
        intersection + EPS
    ) / (
        union + EPS
    )

    # Precision
    true_positive = intersection

    false_positive = np.sum(
        pred * (1 - target)
    )

    precision = (
        true_positive + EPS
    ) / (
        true_positive +
        false_positive +
        EPS
    )

    # Recall
    false_negative = np.sum(
        (1 - pred) * target
    )

    recall = (
        true_positive + EPS
    ) / (
        true_positive +
        false_negative +
        EPS
    )

    total_dice += dice
    total_iou += iou
    total_precision += precision
    total_recall += recall

    num_images += 1


# ==========================================
# 7. FINAL RESULTS
# ==========================================

print("\n==============================")
print("SYNTAX POST-PROCESSED RESULTS")
print("==============================")

print(
    "Test images:",
    num_images
)

print(
    f"Dice Score : "
    f"{total_dice / num_images:.4f}"
)

print(
    f"IoU        : "
    f"{total_iou / num_images:.4f}"
)

print(
    f"Precision  : "
    f"{total_precision / num_images:.4f}"
)

print(
    f"Recall     : "
    f"{total_recall / num_images:.4f}"
)

print("==============================")
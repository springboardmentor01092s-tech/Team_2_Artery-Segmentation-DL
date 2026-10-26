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

        image = cv2.imread(image_path)

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        mask = cv2.imread(
            mask_path,
            cv2.IMREAD_GRAYSCALE
        )

        image = cv2.resize(
            image,
            (IMAGE_SIZE, IMAGE_SIZE)
        )

        mask = cv2.resize(
            mask,
            (IMAGE_SIZE, IMAGE_SIZE),
            interpolation=cv2.INTER_NEAREST
        )

        image = image.astype(np.float32) / 255.0

        mask = (mask > 0).astype(np.float32)

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

        self.conv1 = DoubleConv(3, 32)
        self.conv2 = DoubleConv(32, 64)
        self.conv3 = DoubleConv(64, 128)
        self.conv4 = DoubleConv(128, 256)

        self.pool = nn.MaxPool2d(2)

        self.bottleneck = DoubleConv(
            256,
            512
        )

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

        c1 = self.conv1(x)
        p1 = self.pool(c1)

        c2 = self.conv2(p1)
        p2 = self.pool(c2)

        c3 = self.conv3(p2)
        p3 = self.pool(c3)

        c4 = self.conv4(p3)
        p4 = self.pool(c4)

        b = self.bottleneck(p4)

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
    "dataset/arcade/stenosis/test/images",
    "dataset/arcade/stenosis/test/masks"
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
        "models/unet_stenosis.pth",
        map_location=DEVICE
    )
)

model.eval()

print("Stenosis U-Net loaded successfully!")


# ==========================================
# 6. EVALUATION
# ==========================================

total_intersection = 0
total_union = 0
total_predicted = 0
total_ground_truth = 0
total_true_positive = 0

with torch.no_grad():

    for images, masks in test_loader:

        images = images.to(DEVICE)
        masks = masks.to(DEVICE)

        outputs = model(images)

        probabilities = torch.sigmoid(outputs)

        predictions = (
            probabilities > 0.5
        ).float()

        # Flatten
        predictions = predictions.view(-1)
        masks = masks.view(-1)

        # True positive
        intersection = (
            predictions * masks
        ).sum().item()

        # Union
        union = (
            predictions.sum()
            + masks.sum()
            - intersection
        )

        total_intersection += intersection
        total_union += union

        total_predicted += predictions.sum().item()
        total_ground_truth += masks.sum().item()

        total_true_positive += intersection


# ==========================================
# 7. METRICS
# ==========================================

epsilon = 1e-7

dice = (
    2 * total_intersection
    + epsilon
) / (
    total_predicted
    + total_ground_truth
    + epsilon
)

iou = (
    total_intersection
    + epsilon
) / (
    total_union
    + epsilon
)

precision = (
    total_true_positive
    + epsilon
) / (
    total_predicted
    + epsilon
)

recall = (
    total_true_positive
    + epsilon
) / (
    total_ground_truth
    + epsilon
)


# ==========================================
# 8. PRINT RESULTS
# ==========================================

print("\n================================")
print("STENOSIS U-NET EVALUATION")
print("================================")

print("Test images:", len(test_dataset))

print(f"Dice Score : {dice:.4f}")
print(f"IoU        : {iou:.4f}")
print(f"Precision  : {precision:.4f}")
print(f"Recall     : {recall:.4f}")

print("================================")
import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import random


# ==========================================
# 1. SETTINGS
# ==========================================

IMAGE_SIZE = 256
BATCH_SIZE = 8
EPOCHS = 3
LEARNING_RATE = 0.0005

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", DEVICE)


# ==========================================
# 2. DATASET + AUGMENTATION
# ==========================================

class ArteryDataset(Dataset):

    def __init__(self, image_dir, mask_dir, augment=False):

        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.augment = augment

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

        # ----------------------------------
        # AUGMENTATION
        # ----------------------------------

        if self.augment:

            # Horizontal flip
            if random.random() > 0.5:
                image = np.fliplr(image).copy()
                mask = np.fliplr(mask).copy()

            # Vertical flip
            if random.random() > 0.5:
                image = np.flipud(image).copy()
                mask = np.flipud(mask).copy()

            # Small rotation
            if random.random() > 0.5:

                angle = random.uniform(-10, 10)

                matrix = cv2.getRotationMatrix2D(
                    (IMAGE_SIZE // 2, IMAGE_SIZE // 2),
                    angle,
                    1.0
                )

                image = cv2.warpAffine(
                    image,
                    matrix,
                    (IMAGE_SIZE, IMAGE_SIZE)
                )

                mask = cv2.warpAffine(
                    mask,
                    matrix,
                    (IMAGE_SIZE, IMAGE_SIZE),
                    flags=cv2.INTER_NEAREST
                )

        # ----------------------------------
        # NORMALIZATION
        # ----------------------------------

        image = image.astype(
            np.float32
        ) / 255.0

        mask = (
            mask > 0
        ).astype(np.float32)

        # HWC -> CHW
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
# 3. LIGHTWEIGHT U-NET
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

            nn.BatchNorm2d(
                out_channels
            ),

            nn.ReLU(inplace=True),

            nn.Conv2d(
                out_channels,
                out_channels,
                3,
                padding=1
            ),

            nn.BatchNorm2d(
                out_channels
            ),

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
        u4 = torch.cat(
            [u4, c4],
            dim=1
        )
        d4 = self.dec4(u4)

        u3 = self.up3(d4)
        u3 = torch.cat(
            [u3, c3],
            dim=1
        )
        d3 = self.dec3(u3)

        u2 = self.up2(d3)
        u2 = torch.cat(
            [u2, c2],
            dim=1
        )
        d2 = self.dec2(u2)

        u1 = self.up1(d2)
        u1 = torch.cat(
            [u1, c1],
            dim=1
        )
        d1 = self.dec1(u1)

        return self.final(d1)


# ==========================================
# 4. DICE LOSS
# ==========================================

class DiceLoss(nn.Module):

    def __init__(self):

        super().__init__()

    def forward(self, outputs, targets):

        probabilities = torch.sigmoid(
            outputs
        )

        smooth = 1.0

        intersection = (
            probabilities * targets
        ).sum()

        dice = (
            2.0 * intersection + smooth
        ) / (
            probabilities.sum()
            + targets.sum()
            + smooth
        )

        return 1 - dice


# ==========================================
# 5. DATA
# ==========================================

train_dataset = ArteryDataset(
    "dataset/arcade/syntax/train/images",
    "dataset/arcade/syntax/train/masks",
    augment=True
)

val_dataset = ArteryDataset(
    "dataset/arcade/syntax/val/images",
    "dataset/arcade/syntax/val/masks",
    augment=False
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

print(
    "Training images:",
    len(train_dataset)
)

print(
    "Validation images:",
    len(val_dataset)
)


# ==========================================
# 6. MODEL
# ==========================================

model = UNet().to(DEVICE)

bce_loss = nn.BCEWithLogitsLoss()

dice_loss = DiceLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-4
)


# ==========================================
# 7. TRAINING
# ==========================================

for epoch in range(EPOCHS):

    model.train()

    train_loss = 0.0

    for images, masks in train_loader:

        images = images.to(DEVICE)
        masks = masks.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)

        loss_bce = bce_loss(
            outputs,
            masks
        )

        loss_dice = dice_loss(
            outputs,
            masks
        )

        # Combined loss
        loss = (
            0.5 * loss_bce
            +
            0.5 * loss_dice
        )

        loss.backward()

        optimizer.step()

        train_loss += loss.item()

    train_loss /= len(train_loader)


    # ======================================
    # VALIDATION
    # ======================================

    model.eval()

    val_loss = 0.0

    with torch.no_grad():

        for images, masks in val_loader:

            images = images.to(DEVICE)
            masks = masks.to(DEVICE)

            outputs = model(images)

            loss_bce = bce_loss(
                outputs,
                masks
            )

            loss_dice = dice_loss(
                outputs,
                masks
            )

            loss = (
                0.5 * loss_bce
                +
                0.5 * loss_dice
            )

            val_loss += loss.item()

    val_loss /= len(val_loader)

    print(
        f"Epoch [{epoch+1}/{EPOCHS}] "
        f"Train Loss: {train_loss:.4f} "
        f"Val Loss: {val_loss:.4f}"
    )


# ==========================================
# 8. SAVE MODEL
# ==========================================

os.makedirs(
    "models",
    exist_ok=True
)

torch.save(
    model.state_dict(),
    "models/unet_syntax_optimized.pth"
)

print("\n================================")
print("OPTIMIZED TRAINING COMPLETED")
print("================================")

print(
    "Model saved as:"
    " models/unet_syntax_optimized.pth"
)
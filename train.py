import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


# ==========================================
# 1. SETTINGS
# ==========================================

IMAGE_SIZE = 128
BATCH_SIZE = 4
EPOCHS = 10
LEARNING_RATE = 0.001

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

        # Read mask
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

        # ==============================
        # Encoder
        # ==============================

        self.conv1 = DoubleConv(3, 32)
        self.conv2 = DoubleConv(32, 64)
        self.conv3 = DoubleConv(64, 128)
        self.conv4 = DoubleConv(128, 256)

        self.pool = nn.MaxPool2d(2)

        # ==============================
        # Bottleneck
        # ==============================

        self.bottleneck = DoubleConv(256, 512)

        # ==============================
        # Decoder
        # ==============================

        self.up4 = nn.ConvTranspose2d(
            512, 256, 2, stride=2
        )

        self.dec4 = DoubleConv(
            512, 256
        )

        self.up3 = nn.ConvTranspose2d(
            256, 128, 2, stride=2
        )

        self.dec3 = DoubleConv(
            256, 128
        )

        self.up2 = nn.ConvTranspose2d(
            128, 64, 2, stride=2
        )

        self.dec2 = DoubleConv(
            128, 64
        )

        self.up1 = nn.ConvTranspose2d(
            64, 32, 2, stride=2
        )

        self.dec1 = DoubleConv(
            64, 32
        )

        # Final output
        self.final = nn.Conv2d(
            32, 1, 1
        )


    def forward(self, x):

        # ==============================
        # Encoder
        # ==============================

        c1 = self.conv1(x)
        p1 = self.pool(c1)

        c2 = self.conv2(p1)
        p2 = self.pool(c2)

        c3 = self.conv3(p2)
        p3 = self.pool(c3)

        c4 = self.conv4(p3)
        p4 = self.pool(c4)

        # ==============================
        # Bottleneck
        # ==============================

        b = self.bottleneck(p4)

        # ==============================
        # Decoder
        # ==============================

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
# 4. LOAD SYNTAX DATA
# ==========================================

train_dataset = ArteryDataset(
    "dataset/arcade/syntax/train/images",
    "dataset/arcade/syntax/train/masks"
)

val_dataset = ArteryDataset(
    "dataset/arcade/syntax/val/images",
    "dataset/arcade/syntax/val/masks"
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

print("Training images:", len(train_dataset))
print("Validation images:", len(val_dataset))


# ==========================================
# 5. MODEL
# ==========================================

model = UNet().to(DEVICE)

criterion = nn.BCEWithLogitsLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)


# ==========================================
# 6. TRAINING
# ==========================================

for epoch in range(EPOCHS):

    model.train()

    train_loss = 0

    for images, masks in train_loader:

        images = images.to(DEVICE)
        masks = masks.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(
            outputs,
            masks
        )

        loss.backward()

        optimizer.step()

        train_loss += loss.item()


    train_loss /= len(train_loader)


    # Validation
    model.eval()

    val_loss = 0

    with torch.no_grad():

        for images, masks in val_loader:

            images = images.to(DEVICE)
            masks = masks.to(DEVICE)

            outputs = model(images)

            loss = criterion(
                outputs,
                masks
            )

            val_loss += loss.item()


    val_loss /= len(val_loader)


    print(
        f"Epoch [{epoch+1}/{EPOCHS}] "
        f"Train Loss: {train_loss:.4f} "
        f"Val Loss: {val_loss:.4f}"
    )


# ==========================================
# 7. SAVE MODEL
# ==========================================

os.makedirs("models", exist_ok=True)

torch.save(
    model.state_dict(),
    "models/unet_syntax.pth"
)

print("\nTraining completed!")
print("Model saved as: models/unet_syntax.pth")
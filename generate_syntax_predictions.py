import os
import cv2
import numpy as np
import torch
import torch.nn as nn

# ==========================================
# SETTINGS
# ==========================================

IMAGE_SIZE = 256

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

IMAGE_DIR = "dataset/arcade/syntax/test/images"

OUTPUT_DIR = "dataset/arcade/syntax/test/predicted_masks"

MODEL_PATH = "models/unet_syntax.pth"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Using device:", DEVICE)
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
        self.bottleneck = DoubleConv(256, 512)

        # Decoder
        self.up4 = nn.ConvTranspose2d(
            512, 256, 2, stride=2
        )
        self.dec4 = DoubleConv(512, 256)

        self.up3 = nn.ConvTranspose2d(
            256, 128, 2, stride=2
        )
        self.dec3 = DoubleConv(256, 128)

        self.up2 = nn.ConvTranspose2d(
            128, 64, 2, stride=2
        )
        self.dec2 = DoubleConv(128, 64)

        self.up1 = nn.ConvTranspose2d(
            64, 32, 2, stride=2
        )
        self.dec1 = DoubleConv(64, 32)

        self.final = nn.Conv2d(32, 1, 1)

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
# LOAD TRAINED MODEL
# ==========================================

model = UNet().to(DEVICE)

model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location=DEVICE
    )
)

model.eval()

print("Syntax U-Net loaded successfully!")
# ==========================================
# GENERATE PREDICTED MASKS
# ==========================================

test_images = [
    f for f in os.listdir(IMAGE_DIR)
    if f.lower().endswith(".png")
]

test_images.sort()

print("Test images:", len(test_images))


for image_name in test_images:

    image_path = os.path.join(
        IMAGE_DIR,
        image_name
    )

    image = cv2.imread(image_path)

    if image is None:
        print("Could not read:", image_path)
        continue

    # Convert BGR to RGB
    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    # Resize
    image = cv2.resize(
        image,
        (IMAGE_SIZE, IMAGE_SIZE)
    )

    # Normalize
    image = image.astype(
        np.float32
    ) / 255.0

    # HWC -> CHW
    image = np.transpose(
        image,
        (2, 0, 1)
    )

    # Convert to tensor
    image = torch.tensor(
        image,
        dtype=torch.float32
    ).unsqueeze(0).to(DEVICE)

    # Prediction
    with torch.no_grad():

        output = model(image)

        probability = torch.sigmoid(
            output
        )

    # Convert probability to binary mask
    prediction = (
        probability > 0.5
    ).float()

    # Tensor -> NumPy
    prediction = (
        prediction
        .squeeze()
        .cpu()
        .numpy()
    )

    # Convert to 0-255
    prediction = (
        prediction * 255
    ).astype(np.uint8)

    # Save predicted mask
    output_path = os.path.join(
        OUTPUT_DIR,
        image_name
    )

    cv2.imwrite(
        output_path,
        prediction
    )


print("\n================================")
print("PREDICTION COMPLETED")
print("================================")
print(
    "Predicted masks saved in:",
    OUTPUT_DIR
)
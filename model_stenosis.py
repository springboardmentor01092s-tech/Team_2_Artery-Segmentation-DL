import torch
import torch.nn as nn


# ==========================================
# DOUBLE CONVOLUTION
# ==========================================

class DoubleConv(nn.Module):

    def __init__(self, in_channels, out_channels):

        super().__init__()

        self.block = nn.Sequential(

            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(out_channels),

            nn.ReLU(inplace=True),

            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(out_channels),

            nn.ReLU(inplace=True)
        )

    def forward(self, x):

        return self.block(x)


# ==========================================
# U-NET MODEL
# ==========================================

class UNet(nn.Module):

    def __init__(self):

        super().__init__()

        # Encoder
        self.conv1 = DoubleConv(3, 64)
        self.conv2 = DoubleConv(64, 128)
        self.conv3 = DoubleConv(128, 256)
        self.conv4 = DoubleConv(256, 512)

        self.pool = nn.MaxPool2d(2)

        # Bottleneck
        self.bottleneck = DoubleConv(512, 1024)

        # Decoder
        self.up4 = nn.ConvTranspose2d(
            1024, 512, 2, stride=2
        )

        self.dec4 = DoubleConv(
            1024, 512
        )

        self.up3 = nn.ConvTranspose2d(
            512, 256, 2, stride=2
        )

        self.dec3 = DoubleConv(
            512, 256
        )

        self.up2 = nn.ConvTranspose2d(
            256, 128, 2, stride=2
        )

        self.dec2 = DoubleConv(
            256, 128
        )

        self.up1 = nn.ConvTranspose2d(
            128, 64, 2, stride=2
        )

        self.dec1 = DoubleConv(
            128, 64
        )

        # Final output
        self.final = nn.Conv2d(
            64, 1, 1
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
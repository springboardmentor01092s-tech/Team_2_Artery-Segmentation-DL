"""
Baseline U-Net Architecture for Coronary Artery Segmentation.
Standard encoder-decoder with convolutional blocks, max-pooling, and skip connections.
"""

import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    """Two consecutive conv layers with BatchNorm and ReLU."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class BaselineUNet(nn.Module):
    """Standard U-Net architecture for binary coronary artery segmentation."""

    def __init__(self, in_channels: int = 1, out_channels: int = 1, features: list = None):
        super().__init__()
        if features is None:
            features = [32, 64, 128, 256, 512]

        f1, f2, f3, f4, f5 = features

        # Encoder
        self.enc1 = ConvBlock(in_channels, f1)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.enc2 = ConvBlock(f1, f2)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.enc3 = ConvBlock(f2, f3)
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.enc4 = ConvBlock(f3, f4)
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Bottleneck
        self.bottleneck = ConvBlock(f4, f5)

        # Decoder
        self.up4 = nn.ConvTranspose2d(f5, f4, kernel_size=2, stride=2)
        self.dec4 = ConvBlock(f5, f4)

        self.up3 = nn.ConvTranspose2d(f4, f3, kernel_size=2, stride=2)
        self.dec3 = ConvBlock(f4, f3)

        self.up2 = nn.ConvTranspose2d(f3, f2, kernel_size=2, stride=2)
        self.dec2 = ConvBlock(f3, f2)

        self.up1 = nn.ConvTranspose2d(f2, f1, kernel_size=2, stride=2)
        self.dec1 = ConvBlock(f2, f1)

        # Output projection
        self.final_conv = nn.Conv2d(f1, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder pathway
        e1 = self.enc1(x)
        p1 = self.pool1(e1)

        e2 = self.enc2(p1)
        p2 = self.pool2(e2)

        e3 = self.enc3(p2)
        p3 = self.pool3(e3)

        e4 = self.enc4(p3)
        p4 = self.pool4(e4)

        # Bottleneck
        b = self.bottleneck(p4)

        # Decoder pathway with skip connections
        d4 = self.up4(b)
        d4 = torch.cat([d4, e4], dim=1)
        d4 = self.dec4(d4)

        d3 = self.up3(d4)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        return self.final_conv(d1)


if __name__ == "__main__":
    model = BaselineUNet(in_channels=1, out_channels=1)
    dummy_input = torch.randn(2, 1, 320, 320)
    output = model(dummy_input)
    print("BaselineUNet test output shape:", output.shape)
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total trainable parameters: {num_params:,}")


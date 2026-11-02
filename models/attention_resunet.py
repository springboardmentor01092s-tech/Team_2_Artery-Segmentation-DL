"""
Advanced Attention Residual U-Net for Coronary Artery Segmentation.
Combines residual convolutional blocks with additive attention gates
to focus feature maps on fine coronary vessels while suppressing background noise.
"""

import torch
import torch.nn as nn


class ResidualConvBlock(nn.Module):
    """Residual convolutional block: F(x) + shortcut(x)."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
        )

        if in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.shortcut = nn.Identity()

        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.shortcut(x)
        out = self.conv(x)
        out = self.relu(out + residual)
        return out


class AttentionGate(nn.Module):
    """
    Additive Attention Gate (Oktay et al.).
    Filters features from the encoder skip connection (x) using gating signals (g) from deeper layers.
    """

    def __init__(self, F_g: int, F_l: int, F_int: int):
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(F_g, F_int, kernel_size=1, bias=False),
            nn.BatchNorm2d(F_int),
        )
        self.W_x = nn.Sequential(
            nn.Conv2d(F_l, F_int, kernel_size=1, bias=False),
            nn.BatchNorm2d(F_int),
        )
        self.psi = nn.Sequential(
            nn.Conv2d(F_int, 1, kernel_size=1, bias=False),
            nn.BatchNorm2d(1),
            nn.Sigmoid(),
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, g: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        g1 = self.W_g(g)
        x1 = self.W_x(x)
        psi = self.relu(g1 + x1)
        alpha = self.psi(psi)
        return x * alpha


class AttentionResUNet(nn.Module):
    """
    Attention Residual U-Net:
    Encoder: Residual Conv Blocks + MaxPool
    Skip Connections: Attention Gates
    Decoder: Upsampling + Gated Skip Concat + Residual Conv Blocks
    """

    def __init__(self, in_channels: int = 1, out_channels: int = 1, features: list = None):
        super().__init__()
        if features is None:
            features = [32, 64, 128, 256, 512]

        f1, f2, f3, f4, f5 = features

        # Residual Encoder
        self.enc1 = ResidualConvBlock(in_channels, f1)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.enc2 = ResidualConvBlock(f1, f2)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.enc3 = ResidualConvBlock(f2, f3)
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.enc4 = ResidualConvBlock(f3, f4)
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Residual Bottleneck
        self.bottleneck = ResidualConvBlock(f4, f5)

        # Decoder Stage 4
        self.up4 = nn.ConvTranspose2d(f5, f4, kernel_size=2, stride=2)
        self.att4 = AttentionGate(F_g=f4, F_l=f4, F_int=f4 // 2)
        self.dec4 = ResidualConvBlock(f5, f4)

        # Decoder Stage 3
        self.up3 = nn.ConvTranspose2d(f4, f3, kernel_size=2, stride=2)
        self.att3 = AttentionGate(F_g=f3, F_l=f3, F_int=f3 // 2)
        self.dec3 = ResidualConvBlock(f4, f3)

        # Decoder Stage 2
        self.up2 = nn.ConvTranspose2d(f3, f2, kernel_size=2, stride=2)
        self.att2 = AttentionGate(F_g=f2, F_l=f2, F_int=f2 // 2)
        self.dec2 = ResidualConvBlock(f3, f2)

        # Decoder Stage 1
        self.up1 = nn.ConvTranspose2d(f2, f1, kernel_size=2, stride=2)
        self.att1 = AttentionGate(F_g=f1, F_l=f1, F_int=f1 // 2)
        self.dec1 = ResidualConvBlock(f2, f1)

        # Output projection
        self.final_conv = nn.Conv2d(f1, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder
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

        # Decoder with Attention Gates
        d4 = self.up4(b)
        x4 = self.att4(g=d4, x=e4)
        d4 = torch.cat([d4, x4], dim=1)
        d4 = self.dec4(d4)

        d3 = self.up3(d4)
        x3 = self.att3(g=d3, x=e3)
        d3 = torch.cat([d3, x3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        x2 = self.att2(g=d2, x=e2)
        d2 = torch.cat([d2, x2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        x1 = self.att1(g=d1, x=e1)
        d1 = torch.cat([d1, x1], dim=1)
        d1 = self.dec1(d1)

        return self.final_conv(d1)


if __name__ == "__main__":
    model = AttentionResUNet(in_channels=1, out_channels=1)
    dummy_input = torch.randn(2, 1, 320, 320)
    output = model(dummy_input)
    print("AttentionResUNet test output shape:", output.shape)
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total trainable parameters: {num_params:,}")


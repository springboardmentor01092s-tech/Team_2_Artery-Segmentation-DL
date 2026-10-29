"""CoroVision 3D U-Net architecture recovered from the Kaggle notebook."""
import torch
import torch.nn as nn


class Small3DUNet(nn.Module):
    """Compact binary 3D U-Net; input/output tensors use (B, C, Z, Y, X)."""

    def __init__(self):
        super().__init__()

        self.enc1 = nn.Sequential(
            nn.Conv3d(1, 8, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv3d(8, 8, 3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.pool1 = nn.MaxPool3d(2)

        self.enc2 = nn.Sequential(
            nn.Conv3d(8, 16, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv3d(16, 16, 3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.pool2 = nn.MaxPool3d(2)

        self.bridge = nn.Sequential(
            nn.Conv3d(16, 32, 3, padding=1),
            nn.ReLU(inplace=True),
        )

        self.up2 = nn.ConvTranspose3d(32, 16, 2, stride=2)
        self.dec2 = nn.Sequential(
            nn.Conv3d(32, 16, 3, padding=1),
            nn.ReLU(inplace=True),
        )

        self.up1 = nn.ConvTranspose3d(16, 8, 2, stride=2)
        self.dec1 = nn.Sequential(
            nn.Conv3d(16, 8, 3, padding=1),
            nn.ReLU(inplace=True),
        )

        self.out = nn.Conv3d(8, 1, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        b = self.bridge(self.pool2(e2))

        d2 = self.up2(b)
        d2 = self.dec2(torch.cat([d2, e2], dim=1))

        d1 = self.up1(d2)
        d1 = self.dec1(torch.cat([d1, e1], dim=1))

        return self.out(d1)


# Alias retained for compatibility with earlier CoroVision file names.
CoroVision3DUNet = Small3DUNet


if __name__ == "__main__":
    model = Small3DUNet()
    count = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {count:,}")
    assert count == 48_673, f"Unexpected parameter count: {count}"
    x = torch.randn(1, 1, 16, 32, 32)
    with torch.no_grad():
        y = model(x)
    print("Input:", tuple(x.shape), "Output:", tuple(y.shape))

"""
Lightweight CNN and Clinical Severity Classification Module for Coronary Artery Stenosis.
Calculates QCA Percentage Narrowing and 5-Tier Clinical Severity Categories.
"""

import torch
import torch.nn as nn

SEVERITY_CATEGORIES = ["Normal", "Mild", "Moderate", "Severe", "Total Occlusion"]

SEVERITY_COLORS = {
    "Normal": "#00FFFF",           # Cyan
    "Mild": "#00FF00",             # Green
    "Moderate": "#FFA500",         # Orange
    "Severe": "#FF2020",           # Red
    "Total Occlusion": "#FF00FF",  # Magenta
}


def calculate_percentage_narrowing(reference_diameter: float, min_lumen_diameter: float) -> float:
    """Calculates QCA percentage narrowing: ((RVD - MLD) / RVD) * 100."""
    if reference_diameter <= 0:
        return 0.0
    if min_lumen_diameter <= 0.0:
        return 100.0
    narrowing = ((reference_diameter - min_lumen_diameter) / reference_diameter) * 100.0
    return float(max(0.0, min(100.0, round(narrowing, 2))))


def classify_stenosis_severity(narrowing_pct: float, mld_px: float = None, rvd_px: float = None) -> dict:
    """Classifies coronary stenosis into 5 clinical severity categories."""
    if narrowing_pct >= 99.5 or (mld_px is not None and mld_px <= 0.1):
        sev_class, range_str, grade = "Total Occlusion", "100%", 5
        action = "Complete luminal obstruction (TIMI 0); requires emergent/urgent recanalization"
    elif narrowing_pct >= 70.0:
        sev_class, range_str, grade = "Severe", "70–99%", 4
        action = "Hemodynamically critical; standard candidate for revascularization (PCI/CABG)"
    elif narrowing_pct >= 50.0:
        sev_class, range_str, grade = "Moderate", "50–69%", 3
        action = "Intermediate stenosis; physiological assessment (FFR/iFR) indicated"
    elif narrowing_pct >= 25.0:
        sev_class, range_str, grade = "Mild", "25–49%", 2
        action = "Non-flow-limiting atherosclerotic plaque; aggressive medical management"
    else:
        sev_class, range_str, grade = "Normal", "0–24%", 1
        action = "No hemodynamically significant stenosis"

    return {
        "severity_class": sev_class,
        "severity_range": range_str,
        "severity_grade": grade,
        "color": SEVERITY_COLORS[sev_class],
        "clinical_action": action,
        "narrowing_pct": float(round(narrowing_pct, 1)),
        "mld_px": float(round(mld_px, 2)) if mld_px is not None else None,
        "rvd_px": float(round(rvd_px, 2)) if rvd_px is not None else None,
        "calibration_status": "Pixel estimate (mm requires catheter calibration factor)",
    }


class StenosisClassifier(nn.Module):
    """3-stage CNN classifier for 2-channel (angiogram + mask) vessel patches."""

    def __init__(self, in_channels: int = 2, num_classes: int = 2):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


class StenosisSeverityClassifier(StenosisClassifier):
    """5-Class CNN for direct patch-based coronary stenosis severity grading."""

    def __init__(self, in_channels: int = 2, num_classes: int = 5):
        super().__init__(in_channels=in_channels, num_classes=num_classes)


if __name__ == "__main__":
    m = StenosisClassifier()
    x = torch.randn(2, 2, 48, 48)
    print("StenosisClassifier forward pass:", m(x).shape)
    narrowing = calculate_percentage_narrowing(8.0, 2.0)
    print("Test severity:", classify_stenosis_severity(narrowing, 2.0, 8.0)["severity_class"])

"""Loss functions used by the original CoroVision notebook."""
import torch
import torch.nn as nn
import torch.nn.functional as F


class BCEDiceLoss(nn.Module):
    """Weighted BCE-with-logits + soft Dice loss (notebook default 0.5/0.5)."""

    def __init__(self, bce_weight=0.5, dice_weight=0.5, eps=1e-6):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.bce_weight = float(bce_weight)
        self.dice_weight = float(dice_weight)
        self.eps = float(eps)

    def forward(self, logits, targets):
        bce_loss = self.bce(logits, targets)
        probs = torch.sigmoid(logits.float())
        targets = targets.float()
        dims = (1, 2, 3, 4)
        intersection = (probs * targets).sum(dim=dims)
        denominator = probs.sum(dim=dims) + targets.sum(dim=dims)
        dice = (2 * intersection + self.eps) / (denominator + self.eps)
        dice_loss = 1 - dice.mean()
        return self.bce_weight * bce_loss + self.dice_weight * dice_loss


def dice_score_from_logits(logits, targets, threshold=0.5, eps=1e-6):
    probs = torch.sigmoid(logits.float())
    preds = (probs >= threshold).float()
    targets = targets.float()
    intersection = (preds * targets).sum()
    denominator = preds.sum() + targets.sum()
    return ((2 * intersection + eps) / (denominator + eps)).item()


class TverskyLoss(nn.Module):
    """
    Tversky Loss for addressing severe over-segmentation or under-segmentation.
    alpha > beta penalizes false positives more heavily (ideal for Ven and Young).
    alpha < beta penalizes false negatives more heavily.
    """

    def __init__(self, alpha=0.7, beta=0.3, eps=1e-6):
        super().__init__()
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.eps = float(eps)

    def forward(self, logits, targets):
        probs = torch.sigmoid(logits.float())
        targets = targets.float()
        dims = (1, 2, 3, 4)

        tp = (probs * targets).sum(dim=dims)
        fp = (probs * (1.0 - targets)).sum(dim=dims)
        fn = ((1.0 - probs) * targets).sum(dim=dims)

        tversky = (tp + self.eps) / (tp + self.alpha * fp + self.beta * fn + self.eps)
        return (1.0 - tversky).mean()


class FocalTverskyLoss(nn.Module):
    """Focal Tversky Loss to focus on hard foreground boundary voxels."""

    def __init__(self, alpha=0.7, beta=0.3, gamma=1.33, eps=1e-6):
        super().__init__()
        self.tversky = TverskyLoss(alpha=alpha, beta=beta, eps=eps)
        self.gamma = float(gamma)

    def forward(self, logits, targets):
        tversky_loss = self.tversky(logits, targets)
        return torch.pow(tversky_loss, self.gamma)


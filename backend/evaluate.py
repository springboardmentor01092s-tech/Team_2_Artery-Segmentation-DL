import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from scipy.stats import rankdata

from app.classifier import load_model

DATA = Path(r"D:\artery_app\data\crops\test")
OUT = Path(r"D:\artery_app\backend\weights")
SIZE = 64
THRESHOLD = 0.5            # same cut-off the pipeline uses


def load():
    X, Y = [], []
    for label, cls in enumerate(("normal", "stenosis")):       # normal=0, stenosis=1
        for p in sorted((DATA / cls).glob("*.png")):
            a = np.asarray(Image.open(p).convert("L").resize((SIZE, SIZE)), dtype=np.float32) / 255.0
            X.append(a)
            Y.append(label)
    X = torch.tensor(np.stack(X)).unsqueeze(1)
    return (X - 0.5) / 0.5, np.array(Y)


X, Y = load()
model = load_model()
probs = []
with torch.no_grad():
    for i in range(0, len(X), 256):
        probs.append(torch.softmax(model(X[i:i + 256]), 1)[:, 1].numpy())
probs = np.concatenate(probs)
pred = (probs >= THRESHOLD).astype(int)

tp = int(((pred == 1) & (Y == 1)).sum())
fp = int(((pred == 1) & (Y == 0)).sum())
tn = int(((pred == 0) & (Y == 0)).sum())
fn = int(((pred == 0) & (Y == 1)).sum())
accuracy = (tp + tn) / len(Y)
precision = tp / max(1, tp + fp)
recall = tp / max(1, tp + fn)              # sensitivity
specificity = tn / max(1, tn + fp)
f1 = 2 * precision * recall / max(1e-9, precision + recall)

n_pos, n_neg = int((Y == 1).sum()), int((Y == 0).sum())
ranks = rankdata(probs)
auc = float((ranks[Y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))

metrics = dict(accuracy=accuracy, precision=precision, recall=recall, specificity=specificity,
               f1=f1, auc=auc, tp=tp, fp=fp, tn=tn, fn=fn, n_test=int(len(Y)), threshold=THRESHOLD)
OUT.mkdir(exist_ok=True)
json.dump(metrics, open(OUT / "classifier_metrics.json", "w"), indent=2)

print("TEST RESULTS")
for k in ("accuracy", "precision", "recall", "specificity", "f1", "auc"):
    print(f"  {k:12s}: {metrics[k]:.3f}")
print(f"  confusion matrix  TP={tp}  FP={fp}  TN={tn}  FN={fn}")

# pictures for the report (skipped if matplotlib is missing)
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    order = np.argsort(-probs)
    ys = Y[order]
    tpr = np.concatenate([[0], np.cumsum(ys) / n_pos])
    fpr = np.concatenate([[0], np.cumsum(1 - ys) / n_neg])
    plt.figure(figsize=(4.5, 4.5))
    plt.plot(fpr, tpr, label=f"AUC = {auc:.3f}")
    plt.plot([0, 1], [0, 1], "--", color="grey")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate (sensitivity)")
    plt.title("ROC curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "roc_curve.png", dpi=150)
    plt.close()

    cm = np.array([[tn, fp], [fn, tp]])
    plt.figure(figsize=(4, 4))
    plt.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            plt.text(j, i, cm[i, j], ha="center", va="center", fontsize=14)
    plt.xticks([0, 1], ["normal", "stenosis"])
    plt.yticks([0, 1], ["normal", "stenosis"])
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion matrix")
    plt.tight_layout()
    plt.savefig(OUT / "confusion_matrix.png", dpi=150)
    plt.close()
    print("saved roc_curve.png and confusion_matrix.png in", OUT)
except ImportError:
    print("matplotlib not installed, skipped the pictures")
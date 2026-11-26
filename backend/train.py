import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

DATA = Path(r"D:\artery_app\data\crops")
OUT = Path(r"D:\artery_app\backend\weights")
OUT.mkdir(exist_ok=True)
EPOCHS, BATCH, LR, SIZE = 20, 64, 1e-3, 64
dev = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(0)


def load_split(split):
    X, Y = [], []
    for label, cls in enumerate(("normal", "stenosis")):      # normal=0, stenosis=1
        for p in sorted((DATA / split / cls).glob("*.png")):
            a = np.asarray(Image.open(p).convert("L").resize((SIZE, SIZE)), dtype=np.float32) / 255.0
            X.append(a)
            Y.append(label)
    X = torch.tensor(np.stack(X)).unsqueeze(1)
    return (X - 0.5) / 0.5, torch.tensor(Y)


Xtr, Ytr = load_split("train")
Xva, Yva = load_split("val")
Xte, Yte = load_split("test")
print("train", tuple(Xtr.shape), "| val", tuple(Xva.shape), "| test", tuple(Xte.shape), "| device:", dev)


def augment(x):
    B = x.size(0)
    x = torch.where(torch.rand(B, 1, 1, 1) < 0.5, x.flip(3), x)      # horizontal flip
    x = torch.where(torch.rand(B, 1, 1, 1) < 0.5, x.flip(2), x)      # vertical flip
    c = 1 + (torch.rand(B, 1, 1, 1) - 0.5) * 0.4                      # contrast
    b = (torch.rand(B, 1, 1, 1) - 0.5) * 0.4                          # brightness
    return (x * c + b).clamp(-1, 1)


def block(i, o):
    return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o),
                         nn.ReLU(), nn.MaxPool2d(2))


model = nn.Sequential(
    block(1, 16), block(16, 32), block(32, 64), block(64, 128),
    nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Dropout(0.3), nn.Linear(128, 2),
).to(dev)

counts = torch.bincount(Ytr).float()
weights = (counts.sum() / (2 * counts)).to(dev)          # balance the two classes
loss_fn = nn.CrossEntropyLoss(weight=weights)
opt = torch.optim.Adam(model.parameters(), lr=LR)


def evaluate(X, Y):
    model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, len(X), 256):
            preds.append(model(X[i:i + 256].to(dev)).argmax(1).cpu())
    pred = torch.cat(preds)
    tp = int(((pred == 1) & (Y == 1)).sum())
    fp = int(((pred == 1) & (Y == 0)).sum())
    tn = int(((pred == 0) & (Y == 0)).sum())
    fn = int(((pred == 0) & (Y == 1)).sum())
    acc = (tp + tn) / len(Y)
    prec = tp / max(1, tp + fp)
    rec = tp / max(1, tp + fn)
    f1 = 2 * prec * rec / max(1e-9, prec + rec)
    return dict(accuracy=acc, precision=prec, recall=rec, f1=f1, tp=tp, fp=fp, tn=tn, fn=fn)


best = -1
for ep in range(1, EPOCHS + 1):
    model.train()
    perm = torch.randperm(len(Xtr))
    total = 0.0
    for i in range(0, len(perm), BATCH):
        idx = perm[i:i + BATCH]
        x, y = augment(Xtr[idx]).to(dev), Ytr[idx].to(dev)
        opt.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        opt.step()
        total += loss.item() * len(idx)
    v = evaluate(Xva, Yva)
    print(f"epoch {ep:2d} | loss {total / len(Xtr):.3f} | val acc {v['accuracy']:.3f} | val F1 {v['f1']:.3f}")
    if v["f1"] > best:                         # keep the best epoch by validation F1
        best = v["f1"]
        torch.save(model.state_dict(), OUT / "stenosis_classifier.pt")

model.load_state_dict(torch.load(OUT / "stenosis_classifier.pt"))
t = evaluate(Xte, Yte)                         # test set is used once, at the end
print("\nTEST RESULTS (best epoch)")
for k in ("accuracy", "precision", "recall", "f1"):
    print(f"  {k}: {t[k]:.3f}")
print(f"  confusion matrix  TP={t['tp']}  FP={t['fp']}  TN={t['tn']}  FN={t['fn']}")
json.dump(t, open(OUT / "classifier_metrics.json", "w"), indent=2)
print("saved:", OUT / "stenosis_classifier.pt")
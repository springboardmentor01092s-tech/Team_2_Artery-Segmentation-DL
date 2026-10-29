"""Sliding-window inference for full 3D CT volumes."""
import argparse
from pathlib import Path
import numpy as np
try:
    import SimpleITK as sitk
except ImportError:
    sitk = None
import torch
import torch.nn.functional as F

from .model import Small3DUNet
from .preprocessing import normalize_ct
from .postprocessing import postprocess_prediction


PATCH = (64, 128, 128)
STRIDE = (32, 64, 64)


def _starts(length, patch, stride):
    if length <= patch:
        return [0]
    values = list(range(0, length - patch + 1, stride))
    if values[-1] != length - patch:
        values.append(length - patch)
    return values


@torch.inference_mode()
def predict_volume(model, volume, device, patch_size=PATCH, stride=STRIDE,
                   already_normalized=True):
    """
    Predict probabilities for a (Z,Y,X) volume using overlapping windows.
    Notebook-compatible default expects already-normalized CT.
    Set already_normalized=False for raw Hounsfield units.
    """
    volume = np.asarray(volume, dtype=np.float32)
    if not already_normalized or (volume.min() < -5.0 or volume.max() > 1.5):
        volume = normalize_ct(volume)
    if volume.ndim != 3:
        raise ValueError(f"Expected 3D (Z,Y,X) array, got {volume.shape}")

    original_shape = volume.shape
    pads = [(0, max(0, p - n)) for n, p in zip(volume.shape, patch_size)]
    if any(right for _, right in pads):
        volume = np.pad(volume, pads, mode="constant", constant_values=0)

    shape = volume.shape
    total = np.zeros(shape, dtype=np.float32)
    counts = np.zeros(shape, dtype=np.float32)
    model.eval()

    for z in _starts(shape[0], patch_size[0], stride[0]):
        for y in _starts(shape[1], patch_size[1], stride[1]):
            for x in _starts(shape[2], patch_size[2], stride[2]):
                patch = volume[z:z+patch_size[0], y:y+patch_size[1], x:x+patch_size[2]]
                if patch.shape != patch_size:
                    continue
                tensor = torch.from_numpy(np.ascontiguousarray(patch))[None, None].to(device)
                logits = model(tensor)
                probs = torch.sigmoid(logits.float())[0, 0].cpu().numpy()
                total[z:z+patch_size[0], y:y+patch_size[1], x:x+patch_size[2]] += probs
                counts[z:z+patch_size[0], y:y+patch_size[1], x:x+patch_size[2]] += 1

    probabilities = total / np.maximum(counts, 1)
    return probabilities[:original_shape[0], :original_shape[1], :original_shape[2]]


def load_model(checkpoint_path, device):
    model = Small3DUNet().to(device)
    path = Path(checkpoint_path)
    if path.is_dir():
        import io
        import os
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
            for root, _, files in os.walk(path):
                for f in files:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, path)
                    zf.write(full, f"{path.name}/" + rel.replace(os.sep, "/"))
        buf.seek(0)
        checkpoint = torch.load(buf, map_location=device, weights_only=True)
    else:
        checkpoint = torch.load(path, map_location=device, weights_only=True)
    state = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state, strict=True)
    model.eval()
    return model, checkpoint


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Normalized CT NIfTI by default")
    parser.add_argument("--checkpoint", default="checkpoints/best_corovision_3d_unet.pth")
    parser.add_argument("--output", default="results/predicted_mask.nii.gz")
    parser.add_argument("--raw-ct", action="store_true", help="Normalize raw HU input first")
    parser.add_argument("--threshold", type=float, default=0.5, help="Probability threshold (default: 0.5)")
    parser.add_argument("--lcc", action="store_true", help="Filter connected components to prune false positives")
    parser.add_argument("--postprocess-mode", choices=["major", "lcc", "filter_small", "none"], default="major",
                        help="Component filtering mode: 'major' preserves largest + major branches, 'lcc' is single largest")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if sitk is None:
        raise ImportError("SimpleITK is required for NIfTI image operations. Install with: pip install SimpleITK")
    image = sitk.ReadImage(args.image)
    volume = sitk.GetArrayFromImage(image).astype(np.float32)
    model, checkpoint = load_model(args.checkpoint, device)
    probs = predict_volume(model, volume, device, already_normalized=not args.raw_ct)
    pp_mode = args.postprocess_mode if args.lcc else "none"
    prediction = postprocess_prediction(probs, threshold=args.threshold, apply_lcc=args.lcc, mode=pp_mode)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    mask_image = sitk.GetImageFromArray(prediction)
    mask_image.CopyInformation(image)
    sitk.WriteImage(mask_image, str(output))
    print("Device:", device)
    print("Checkpoint epoch:", checkpoint.get("epoch", "unknown"))
    print("Prediction shape:", prediction.shape)
    print("Foreground voxels:", int(prediction.sum()))
    print("Saved:", output)


if __name__ == "__main__":
    main()

"""Package a train/validation-only ARCADE COCO bundle for the Colab notebook."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "colab" / "corovision_arcade_instance_bundle.zip")
    args = parser.parse_args()
    files = [ROOT / "scripts" / "train_arcade_instances.py"]
    files += [ROOT / "backend" / "requirements-ai.txt"]
    for task in ("syntax", "stenosis"):
        for split in ("train", "val"):
            data_root = ROOT / "arcade" / task / split
            files += sorted(path for path in data_root.rglob("*") if path.is_file())
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise SystemExit("Missing required files:\n" + "\n".join(missing))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT))
    print(f"Wrote {args.output} ({args.output.stat().st_size / 1024**2:.1f} MiB; {len(files)} files)")
    with ZipFile(args.output) as archive:
        names = archive.namelist()
        if any("/test/" in name for name in names):
            raise SystemExit("Refusing bundle that contains test split data")
        if not any(name.endswith("/annotations/train.json") for name in names):
            raise SystemExit("COCO training annotations were not packaged")
        if not any(name.endswith("/annotations/val.json") for name in names):
            raise SystemExit("COCO validation annotations were not packaged")


if __name__ == "__main__":
    main()

"""Prepare one existing public ARCADE training frame as an upload example."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.preprocessing import prepare_image, content_geometry
from PIL import Image

source = ROOT / "arcade/syntax/train/images/573.png"
destination = ROOT / "output/upload_example"
destination.mkdir(parents=True, exist_ok=True)
original = destination / "ARCADE_training_example.png"
shutil.copyfile(source, original)
steps = ["public_ARCADE_training_frame", "file_decode_validation"]
preview, width, height, media_type, spacing = prepare_image(
    original.read_bytes(), original.name, denoise=True, enhance=True, processing_steps=steps)
assert Image.open(BytesIO(preview)).size == (512, 512)
(destination / "preprocessed_example.png").write_bytes(preview)
record = {"source": "ARCADE syntax training frame 573; not a patient diagnosis",
          "source_file": str(source), "profile": "research", "denoise": True, "enhance": True,
          "original_dimensions": [width, height], "preview_dimensions": [512, 512],
          "spacing_mm": spacing, "spacing_note": "Not supplied by source PNG; not invented",
          "geometry": content_geometry(width, height), "steps": steps,
          "source_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
          "preview_sha256": hashlib.sha256(preview).hexdigest(),
          "verification": "Decoded and prepared successfully with the application preprocessing function",
          "training_started": False}
(destination / "processing_record.json").write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))

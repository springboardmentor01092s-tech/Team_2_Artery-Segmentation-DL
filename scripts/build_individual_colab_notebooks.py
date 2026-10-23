"""Build self-contained ARCADE notebooks from the existing verified scripts."""
from __future__ import annotations

import base64
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build() -> list[Path]:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as bundle:
        for relative in ("ml/__init__.py", "ml/preprocessing/__init__.py", "ml/preprocessing/pipeline.py",
                         "ml/preprocessing/model_input.py", "ml/preprocessing/run_preprocessing.py",
                         "ml/preprocessing/configs/arcade_preprocessing.json", "scripts/run_dataset_eda.py",
                         "scripts/train_arcade_instances.py"):
            bundle.write(ROOT / relative, relative)
    payload = base64.b64encode(buffer.getvalue()).decode()
    paths = []
    for task in ("syntax", "stenosis"):
        cells = []
        def md(text):
            cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)})
        def code(text):
            cells.append({"cell_type": "code", "metadata": {}, "execution_count": None,
                          "outputs": [], "source": text.splitlines(True)})
        md(f"# CoroVision ARCADE {task}: individual training\n"
           "Downloads the official release, verifies its published MD5, validates both tasks, performs EDA, "
           f"then trains only **{task}** using original polygons and source classes. "
           "Select a free T4 GPU runtime. Download checkpoints before the runtime expires. "
           "Official test data is audited but never used for fitting or selection. "
           "No severity labels are invented. Dataset: https://zenodo.org/records/10390295")
        code("import base64, io, zipfile, pathlib, subprocess, sys, hashlib, json\n"
             "PROJECT = pathlib.Path('/content/corovision_individual')\nPROJECT.mkdir(exist_ok=True)\n"
             f"PAYLOAD = {payload!r}\n"
             "with zipfile.ZipFile(io.BytesIO(base64.b64decode(PAYLOAD))) as archive:\n"
             "    archive.extractall(PROJECT)\n"
             "subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'Pillow>=10', 'numpy', 'shapely>=2', 'opencv-python-headless'], check=True)\n"
             "import torch, torchvision\nprint('Torch', torch.__version__, 'CUDA', torch.cuda.is_available())\n")
        code("archive_path = PROJECT / 'arcade.zip'\n"
             "subprocess.run(['curl', '-fL', '--retry', '6', '--retry-all-errors', '-C', '-', '-o', str(archive_path), "
             "'https://zenodo.org/records/10390295/files/arcade.zip?download=1'], check=True)\n"
             "digest = hashlib.md5()\nwith archive_path.open('rb') as f:\n"
             "    for block in iter(lambda: f.read(1024*1024), b''): digest.update(block)\n"
             "assert digest.hexdigest() == 'c5b1973ade06f7dff210f878161e1a76', 'Archive checksum mismatch'\n"
             "with zipfile.ZipFile(archive_path) as z:\n"
             "    for member in z.infolist():\n"
             "        target = (PROJECT / member.filename).resolve()\n"
             "        assert target.is_relative_to(PROJECT.resolve()), 'Unsafe archive path'\n"
             "    assert z.testzip() is None, 'ZIP CRC validation failed'\n"
             "    z.extractall(PROJECT)\n"
             "assert (PROJECT / 'arcade/syntax/train/images').is_dir(), 'Unexpected dataset layout'\n")
        code("subprocess.run([sys.executable, '-m', 'ml.preprocessing.run_preprocessing', '--data-root', 'arcade', "
             "'--output-root', 'data/processed/arcade'], cwd=PROJECT, check=True)\n"
             "report = json.loads((PROJECT/'data/processed/arcade/reports/inventory.json').read_text())\n"
             "assert report['status'] != 'fail', 'Preprocessing failed: training blocked'\n"
             "subprocess.run([sys.executable, 'scripts/run_dataset_eda.py', '--data-root', 'arcade', '--output-root', 'outputs/eda'], cwd=PROJECT, check=True)\n"
             "print(json.dumps(report['issue_counts'], indent=2))\n")
        md("## Training gate\nPreprocessing and EDA must succeed first. Training uses train and validation only. "
           "Decoded-image duplicates are explicitly excluded from the training loader while validation remains fixed. "
           "Checkpoints, per-class validation scores and logs are stored per task/architecture. "
           "The test set is reserved for final evaluation after model selection.")
        code("assert torch.cuda.is_available(), 'Training blocked: select a free T4 GPU runtime'\n"
             "print('GPU:', torch.cuda.get_device_name(0))\n"
             f"TASK = {task!r}\n"
             "subprocess.run([sys.executable, 'scripts/train_arcade_instances.py', '--task', TASK, "
             "'--architectures', 'maskrcnn_resnet50_fpn', '--epochs', '25', '--batch-size', '2', "
             "'--workers', '2', '--seed', '42', '--patience', '6', '--output-dir', f'models/individual/{TASK}'], cwd=PROJECT, check=True)\n")
        code("import shutil\nfrom google.colab import files\n"
             "result_path = shutil.make_archive(f'/content/corovision_{TASK}_results', 'zip', PROJECT, f'models/individual/{TASK}')\n"
             "files.download(result_path)\n")
        path = ROOT / "colab" / f"ARCADE_{task}_individual.ipynb"
        path.write_text(json.dumps({"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"accelerator": "GPU", "kernelspec": {"display_name": "Python 3", "name": "python3"}},
            "cells": cells}, indent=1))
        paths.append(path)
    return paths


if __name__ == '__main__':
    for path in build():
        print(path)

"""Validate and prepare the authors' ICA PNG release without assuming clean masks."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def prepare(archive: Path, output: Path) -> dict:
    """Keep all source masks losslessly and report categorical-mask ambiguities."""
    rows, issues = [], []
    dimensions, modes, mask_values = Counter(), Counter(), Counter()
    means, foreground, previews = [], [], []
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('ICA ZIP failed CRC validation')
        images = {Path(n).name: n for n in z.namelist() if '/ICA_PNG/' in n and n.lower().endswith('.png')}
        masks = {Path(n).name: n for n in z.namelist() if '/label/' in n and n.lower().endswith('.png')}
        if not images or set(images) != set(masks):
            raise ValueError(f'ICA pairing mismatch: missing masks={set(images)-set(masks)}, missing images={set(masks)-set(images)}')
        for folder in ('images', 'source_masks', 'qa'):
            (output / folder).mkdir(parents=True, exist_ok=True)
        for filename in sorted(images):
            raw_image, raw_mask = z.read(images[filename]), z.read(masks[filename])
            with Image.open(io.BytesIO(raw_image)) as opened:
                opened.load(); source_mode = opened.mode
                image = opened.convert('L')
            with Image.open(io.BytesIO(raw_mask)) as opened:
                opened.load(); mask = opened.copy()
            if image.size != mask.size:
                raise ValueError(f'{filename}: image/mask geometry differs')
            array = np.asarray(image)
            rgb_mask = np.asarray(mask.convert('RGB'))
            channels_equal = bool(np.array_equal(rgb_mask[...,0], rgb_mask[...,1]) and np.array_equal(rgb_mask[...,0], rgb_mask[...,2]))
            values, counts = np.unique(rgb_mask[...,0], return_counts=True)
            mask_values.update(dict(zip(map(int, values), map(int, counts))))
            fractional = bool(np.any((values != 0) & (values != 255)))
            if fractional:
                issues.append({'sample_id': Path(filename).stem, 'type': 'non_binary_source_mask',
                               'explanation': 'Source described as binary but contains intermediate intensities; preserved unchanged, no threshold guessed.'})
            if not channels_equal:
                issues.append({'sample_id': Path(filename).stem, 'type': 'unequal_mask_channels',
                               'explanation': 'RGB label semantics require source clarification.'})
            image.save(output/'images'/filename)
            mask.save(output/'source_masks'/filename)
            dimensions[str(image.size)] += 1; modes[source_mode] += 1
            means.append(float(array.mean())); foreground.append(float((rgb_mask[...,0] == 255).mean()))
            rows.append({'sample_id': Path(filename).stem, 'source_archive_image': images[filename],
                         'source_archive_mask': masks[filename], 'image_path': f'images/{filename}',
                         'mask_path': f'source_masks/{filename}', 'width': image.width, 'height': image.height,
                         'image_sha256': hashlib.sha256(raw_image).hexdigest(), 'mask_sha256': hashlib.sha256(raw_mask).hexdigest(),
                         'mask_intermediate_values': fractional, 'spacing_status': 'unavailable_in_png',
                         'split': 'unassigned_pending_verified_patient_groups'})
            if len(previews) < 6:
                preview = image.convert('RGB')
                tint = Image.new('RGBA', image.size, (255, 45, 45, 0))
                tint.putalpha(mask.convert('L').point(lambda x: round(x * .45)))
                previews.append((filename, Image.alpha_composite(preview.convert('RGBA'), tint).convert('RGB')))
        commit = z.comment.decode(errors='replace')
    hashes = Counter(row['image_sha256'] for row in rows)
    summary = {'dataset': 'ICA_NJ_BinarySeg', 'archive': str(archive), 'source_commit': commit,
               'image_mask_pairs': len(rows), 'dimensions': dict(dimensions), 'source_modes': dict(modes),
               'image_mean_intensity': {'min': min(means), 'mean': float(np.mean(means)), 'max': max(means)},
               'source_255_pixel_fraction': {'min': min(foreground), 'mean': float(np.mean(foreground)), 'max': max(foreground)},
               'mask_value_pixel_counts': dict(mask_values), 'intermediate_mask_count': sum(r['mask_intermediate_values'] for r in rows),
               'exact_image_duplicate_groups': sum(n > 1 for n in hashes.values()),
               'issues': issues, 'training_ready': False,
               'training_blockers': ['Verify data reuse terms; repository has no explicit dataset licence.',
                                     'Resolve intermediate-intensity mask semantics before binarization.',
                                     'Verify patient grouping and create documented patient-level splits.']}
    (output/'eda_summary.json').write_text(json.dumps(summary, indent=2))
    with (output/'manifest.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    sheet = Image.new('RGB', (1024, 3*536), 'white'); draw = ImageDraw.Draw(sheet)
    for index, (name, preview) in enumerate(previews):
        x, y = index % 2 * 512, index // 2 * 536
        sheet.paste(preview.resize((512,512)), (x,y+24)); draw.text((x+5,y+5), name, fill='black')
    sheet.save(output/'qa/source_label_overlays.jpg')
    print(json.dumps({key: summary[key] for key in ('image_mask_pairs','intermediate_mask_count','training_ready','training_blockers')}, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=Path('data/raw/ica/ICA_NJ_BinarySeg_master.zip'))
    parser.add_argument('--output', type=Path, default=Path('data/processed/ica'))
    args = parser.parse_args()
    prepare(args.archive, args.output)

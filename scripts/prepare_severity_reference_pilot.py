"""Prepare a local, prediction-free ARCADE pilot for independent measurement.

The output is annotation preparation, not a locked reference cohort. Images are
kept outside the publish checkout because dataset assets must not be published.
"""
from collections import defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw


SOURCE = Path('/Volumes/One Touch/artertry segmentation/Dataset/2D/ARCADE/stenosis/test')
OUTPUT = Path('/Volumes/One Touch/execution_readiness_20261030/corovision_severity_reference_pilot_20261110')
COUNT = 20


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    coco_path = SOURCE / 'annotations/test.json'
    coco = json.loads(coco_path.read_text())
    annotations = defaultdict(list)
    for annotation in coco['annotations']:
        if annotation['category_id'] == 26:
            annotations[annotation['image_id']].append(annotation)
    candidates = [image for image in coco['images'] if len(annotations[image['id']]) == 1]
    candidates.sort(key=lambda image: int(Path(image['file_name']).stem))
    if len(candidates) < COUNT:
        raise RuntimeError('Not enough single-annotation candidate frames')
    positions = [round(index * (len(candidates) - 1) / (COUNT - 1)) for index in range(COUNT)]
    selected = [candidates[position] for position in positions]
    if len({image['id'] for image in selected}) != COUNT:
        raise RuntimeError('Pilot selection is not unique')

    for directory in ('images', 'annotation_overlays'):
        (OUTPUT / directory).mkdir(parents=True, exist_ok=True)
    manifest_rows, worksheet_rows = [], []
    for image_record in selected:
        source = SOURCE / 'images' / image_record['file_name']
        annotation = annotations[image_record['id']][0]
        target = OUTPUT / 'images' / image_record['file_name']
        shutil.copy2(source, target)
        image = Image.open(source).convert('RGB')
        draw = ImageDraw.Draw(image)
        for polygon in annotation.get('segmentation') or []:
            points = list(zip(polygon[0::2], polygon[1::2]))
            if len(points) >= 3:
                draw.line([*points, points[0]], fill=(255, 214, 10), width=2)
        x, y, width, height = annotation['bbox']
        draw.rectangle((x, y, x + width, y + height), outline=(255, 64, 64), width=2)
        overlay = OUTPUT / 'annotation_overlays' / image_record['file_name']
        image.save(overlay)
        lesion_id = f"ARCADE-test-{image_record['id']}-ann-{annotation['id']}"
        common = dict(candidate_status='candidate_only_checkpoint_exposed', source_dataset='ARCADE stenosis test',
            source_split='test', source_image_id=image_record['id'], frame_id=image_record['file_name'],
            lesion_id=lesion_id, annotation_id=annotation['id'], annotation_bbox_xywh=json.dumps(annotation['bbox']),
            annotation_polygon=json.dumps(annotation.get('segmentation') or []), width=image_record['width'],
            height=image_record['height'], source_image_sha256=digest(source),
            local_source_path=str(source), package_image_path=str(target), overlay_path=str(overlay),
            checkpoint_independence='not_eligible_ARCADE_cohort_exposure_established',
            licence_status='local_COCO_license_fields_blank_verify_official_terms_before_redistribution')
        manifest_rows.append(common)
        worksheet_rows.append({**common, 'vessel_segment':'', 'minimum_location_original_xy':'',
            'reference_location_original_xy':'', 'reference_mld':'', 'reference_rvd':'',
            'diameter_unit':'source_px', 'calibration_source':'unavailable',
            'reference_selection_method':'', 'measurement_method':'Fiji/ImageJ blinded manual measurement',
            'annotator_id':'', 'measured_at':'', 'quality_status':'pending_independent_measurement',
            'exclusion_reason':'', 'reference_version':'pilot-unlocked', 'independent_of_corovision':''})

    def write_csv(path, rows):
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    write_csv(OUTPUT / 'candidate_manifest.csv', manifest_rows)
    write_csv(OUTPUT / 'measurement_worksheet.csv', worksheet_rows)
    readme = """# CoroVision severity reference pilot - annotation preparation

This local package contains 20 deterministically sampled ARCADE stenosis test frames with exactly one COCO stenosis annotation each. Yellow/red overlays reproduce only the supplied dataset polygon/bounding box; they contain no CoroVision prediction.

Status: candidate-only, unlocked, zero independently measured lesions, zero verified physical calibrations. ARCADE cohort exposure to the frozen checkpoints is established, so these frames are not confirmed external test data. The local COCO license fields are blank; verify official terms before redistribution.

Independent reviewer instructions:

1. Work from `images/`, using `annotation_overlays/` only to identify the dataset lesion after opening the original frame.
2. Remain blinded to CoroVision masks, width profiles and predictions.
3. In Fiji/ImageJ, mark the minimum lumen cross-section perpendicular to the local vessel direction.
4. Mark a suitable reference cross-section using the same method and original-image coordinate frame.
5. Keep `source_px` unless a valid image-plane calibration source is independently verified.
6. Complete reviewer/method, locations, widths, quality and exclusion fields in `measurement_worksheet.csv`.
7. Do not mark `independent_of_corovision=true` unless the measurements and locations were established without CoroVision output.
8. Return the worksheet for validation and locking. Do not edit images or the candidate manifest.
"""
    (OUTPUT / 'README.md').write_text(readme)
    for sidecar in OUTPUT.rglob('._*'):
        if sidecar.is_file():
            sidecar.unlink()
    inventory_paths = sorted(path for path in OUTPUT.rglob('*') if path.is_file() and path.name not in {'package_receipt.json', 'package_files.sha256'})
    inventory_text = ''.join(f"{digest(path)}  {path.relative_to(OUTPUT)}\n" for path in inventory_paths)
    (OUTPUT / 'package_files.sha256').write_text(inventory_text)
    receipt = {'schema_version': 1, 'status': 'candidate_only_unlocked', 'source': str(SOURCE),
        'source_coco_sha256': digest(coco_path), 'selected_images': COUNT,
        'candidate_lesions': len(manifest_rows), 'independently_measured': 0,
        'verified_physical_calibration': 0, 'images_sha256': digest(OUTPUT / 'candidate_manifest.csv'),
        'worksheet_sha256': digest(OUTPUT / 'measurement_worksheet.csv'),
        'package_file_count': len(inventory_paths),
        'package_inventory_sha256': digest(OUTPUT / 'package_files.sha256'),
        'selection': '20 evenly spaced numeric filenames among category-26 images having exactly one annotation',
        'checkpoint_independence': 'not eligible; ARCADE cohort exposure established',
        'licence_status': 'local COCO fields blank; official terms must be verified before redistribution'}
    (OUTPUT / 'package_receipt.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

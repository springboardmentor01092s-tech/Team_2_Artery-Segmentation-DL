"""Run-bound visualization inventory; never inference or illustrative substitutes."""
from io import BytesIO
from pathlib import Path

PANELS = [
    ('original', 'Original coronary angiography', 'Uploaded source image; not a model prediction.'),
    ('landmarks', 'Vessel annotation / landmarks', 'No saved landmark or control-point annotations are available for this run.'),
    ('centerline', 'Centerline visualization', 'Saved algorithmic centerline derived from the predicted artery mask; not verified anatomical branches.'),
    ('boundary', 'Vessel boundary visualization', 'Contour derived from the saved binary artery mask, shown in prepared-image coordinates. Not a new model prediction.'),
    ('processed', 'Processed angiography', 'Saved model-input preview after preprocessing; resizing and padding may differ from the original.'),
    ('artery_mask', 'Binary artery segmentation mask', 'Saved predicted artery pixels; not a ground-truth annotation.'),
    ('overlay', 'Predicted segmentation overlay', 'Saved model overlay in the prepared-image frame; not necessarily registered to the original source grid.'),
    ('artery_probability', 'Artery probability evidence', 'Saved uncalibrated artery pixel scores. Colour intensity is not patient-level confidence.'),
    ('probability', 'Stenosis probability evidence', 'Saved score-weighted stenosis mask evidence. Colour intensity is not severity or diagnostic confidence.'),
    ('attention', 'Detector feature activation', 'Saved backbone activation energy for compatible detector runs. This is not an attention-gate weight or a clinically validated explanation.'),
    ('gradcam', 'Grad-CAM attribution', 'Available only when the saved model has a verified target and convolutional layer contract. Not a clinical explanation.'),
    ('gradcampp', 'Grad-CAM++ attribution', 'Second-order Grad-CAM weighting of the same detector targets; better coverage when several candidates are present. Not a clinical explanation.'),
]


def paths(image, event):
    overlay = Path(event.overlay_path)
    return {'original': Path(image.original_path), 'processed': Path(image.preview_path),
            'overlay': overlay, 'centerline': overlay.with_name(f'{overlay.stem}.centerline.png'),
            'artery_mask': overlay.with_name(f'{event.id}.artery_mask.png'),
            'artery_probability': overlay.with_name(f'{overlay.stem}.artery_probability.png'),
            'probability': overlay.with_name(f'{overlay.stem}.probability.png'),
            'attention': overlay.with_name(f'{overlay.stem}.attention.png'),
            'gradcam': overlay.with_name(f'{overlay.stem}.gradcam.png'),
            'gradcampp': overlay.with_name(f'{overlay.stem}.gradcampp.png')}


def inventory(image, event):
    files = paths(image, event)
    base = f'/api/images/{image.id}/analyses/{event.id}/panels/'
    return [dict(key=key, title=title, description=description,
                 available=bool(files.get('artery_mask' if key == 'boundary' else key) and
                                files['artery_mask' if key == 'boundary' else key].is_file()),
                 url=None if key == 'landmarks' else base+key)
            for key, title, description in PANELS]


def boundary_png(mask_path):
    from PIL import Image, ImageFilter, ImageChops
    with Image.open(mask_path) as source:
        mask = source.convert('L').point(lambda value: 255 if value else 0)
    # Inner morphological contour, no smoothing or changed prediction pixels.
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(3)))
    output = BytesIO()
    edge.save(output, format='PNG')
    return output.getvalue()


def printable_original(image):
    """Return a ReportLab-compatible source without altering retained uploads."""
    path = Path(image.original_path)
    name = str(getattr(image, 'original_name', '') or path.name).lower()
    if name.endswith(('.dcm', '.dicom')) or path.suffix.lower() in {'.dcm', '.dicom'}:
        from .preprocessing import source_grayscale
        decoded = source_grayscale(path.read_bytes(), name, getattr(image, 'frame_index', None))
        output = BytesIO()
        decoded.save(output, format='PNG')
        output.seek(0)
        return output
    return path


def report_images(image, event, panels=None):
    """Select the source and overlay for the printable summary."""
    files = paths(image, event)
    rows = []
    for panel in panels or inventory(image, event):
        key = panel['key']
        if key in {'original', 'overlay'}:
            source = printable_original(image) if key == 'original' else files.get(key)
            rows.append((panel['title']+' — '+panel['description'], source))
    return rows

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
]


def paths(image, event):
    overlay = Path(event.overlay_path)
    return {'original': Path(image.original_path), 'processed': Path(image.preview_path),
            'overlay': overlay, 'centerline': overlay.with_name(f'{overlay.stem}.centerline.png'),
            'artery_mask': overlay.with_name(f'{event.id}.artery_mask.png')}


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


def report_images(image, event, panels=None):
    """PDF consumes the same saved inventory as the browser, including missing slots."""
    files = paths(image, event)
    rows = []
    for panel in panels or inventory(image, event):
        key = panel['key']
        path = files.get(key)
        if key == 'boundary' and files['artery_mask'].is_file():
            path = BytesIO(boundary_png(files['artery_mask']))
        rows.append((panel['title']+' — '+panel['description'], path))
    return rows

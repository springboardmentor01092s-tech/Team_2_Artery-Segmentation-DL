"""Hash-pinned preserved training artifacts for the existing mask-analysis contract."""
import hashlib
import importlib.util
import json
import os
from functools import lru_cache
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[2]
RELEASE = json.loads((ROOT / 'ml/releases/corovision_20261023.json').read_text())
LOCK = threading.Lock()


def artifact_root():
    return Path(os.environ.get('COROVISION_TRAINED_RELEASE', ROOT / 'models/trained_release')).resolve()


def configured():
    if os.environ.get('COROVISION_MODEL_PROVIDER') == 'legacy':
        return False
    return bool(os.environ.get('COROVISION_TRAINED_RELEASE')) or artifact_root().exists()


@lru_cache(maxsize=4)
def _verify(root, signature):
    for item in RELEASE['models']:
        path = Path(root) / item['filename']
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != item['sha256']:
                raise ValueError('Trained model hash mismatch: ' + item['task'])
    return True


def ready():
    try:
        if not all(importlib.util.find_spec(x) for x in ['torch', 'torchvision', 'cv2', 'scipy']):
            return False
        root = artifact_root()
        signature = tuple((p.stat().st_size, p.stat().st_mtime_ns) for p in
                          [root / item['filename'] for item in RELEASE['models']])
        return _verify(str(root), signature)
    except (OSError, ValueError, ImportError):
        return False


def status():
    return dict(version=RELEASE['version'], configured=configured(), ready=ready() if configured() else False,
                input_contract='512x512 prepared coronary X-ray; grayscale0..1 artery,RGB0..1 stenosis; no extra autocontrast or morphology',
                models=RELEASE['models'], limitations=RELEASE['limitations'], research_only=True,
                research_evidence=json.loads((ROOT / 'ml/releases/research_evidence_20261023.json').read_text()),
                clinical_calibration=False, training_controls_connected=False)


@lru_cache(maxsize=2)
def _models(root):
    import torch
    from .preserved_models import PretrainedVesselUNet, build_detector
    if not ready():
        raise ValueError('Install the verified trained release and optional inference dependencies')
    torch.set_num_threads(2)
    artery = PretrainedVesselUNet(False)
    artery.load_state_dict(torch.load(Path(root) / 'artery.pt', map_location='cpu', weights_only=True)['model'])
    checkpoint = torch.load(Path(root) / 'stenosis.pt', map_location='cpu', weights_only=True)
    if checkpoint['architecture'] != 'maskrcnn_resnet50_fpn' or checkpoint['num_classes'] != 2:
        raise ValueError('Unexpected stenosis architecture/class map')
    stenosis = build_detector(checkpoint['architecture'], checkpoint['num_classes'], pretrained=False)
    stenosis.load_state_dict(checkpoint['state_dict'])
    return artery.eval(), stenosis.eval()


def predict_masks(path):
    import numpy as np
    import torch
    from PIL import Image
    from .preserved_models import predict_one
    if not ready():
        raise ValueError('Trained release unavailable or hash verification failed')
    with Image.open(path) as opened:
        rgb = opened.convert('RGB')
        if rgb.size != (512, 512):
            raise ValueError('The trained release requires the application512x512 prepared preview')
        gray = np.asarray(rgb.convert('L'), dtype=np.float32) / 255.
        color = np.asarray(rgb, dtype=np.float32).copy() / 255.
    with LOCK:
        artery_model, stenosis_model = _models(str(artifact_root()))
        with torch.inference_mode():
            artery_probability = artery_model(torch.from_numpy(gray.copy())[None, None]).sigmoid()[0, 0].numpy()
        instances = predict_one(stenosis_model, torch.from_numpy(color.transpose(2, 0, 1).copy()), 'cpu', .1)
    artery = artery_probability >= .5
    stenosis = np.zeros_like(artery)
    probability = np.zeros_like(artery_probability)
    records = []
    for item in instances:
        if item['category_id'] != 1:
            raise ValueError('Invalid stenosis foreground label')
        stenosis |= item['mask']
        probability = np.maximum(probability, item['mask_probability'])
        y, x = np.where(item['mask'])
        records.append(dict(candidate_id=f'C{len(records)+1}', task='ARCADE stenosis instance mask',
                            category_id=26, model_score=item['score'],
                            bbox_prepared_xyxy=[int(x.min()), int(y.min()), int(x.max())+1, int(y.max())+1],
                            polygon_prepared_xy=item['polygon'], coordinate_frame='prepared_512_xy',
                            mask_pixels=int(item['mask'].sum()), calibration='uncalibrated_raw_score'))
    return artery, stenosis, artery_probability, probability, records


def analyze(path, spacing_mm=None):
    from io import BytesIO
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    from .analysis_model import analyze_vessel_geometry, centerline_overlay_png, heatmap_overlay_png, overlay_png
    artery, stenosis, artery_p, stenosis_p, instances = predict_masks(path)
    if any(value.shape != (512, 512) for value in [artery, stenosis, artery_p, stenosis_p]):
        raise ValueError('Unexpected prediction geometry')
    if any(not np.isfinite(value).all() or np.any((value < 0) | (value > 1)) for value in [artery_p, stenosis_p]):
        raise ValueError('Invalid raw prediction scores')
    geometry = analyze_vessel_geometry(artery, spacing_mm, artery_p, .5)
    geometry['stenosis_mask_components'] = int(ndimage.label(stenosis)[1])
    geometry['stenosis_component_interpretation'] = 'Predicted mask components,not confirmed lesions.'
    scores = dict(artery_foreground_mean_probability=float(artery_p[artery].mean()) if artery.any() else None,
                  stenosis_foreground_mean_probability=float(stenosis_p[stenosis].mean()) if stenosis.any() else None,
                  calibration='uncalibrated_raw_pixel_and_instance_scores', instance_detections=instances,
                  trained_release=RELEASE['version'], checkpoint_sha256={x['task']: x['sha256'] for x in RELEASE['models']},
                  preprocessing='Preserved512contract; no median/autocontrast/postprocessing added',
                  absence_interpretation='No detections do not establish absence of disease')
    # Private artifacts are consumed by the API, never serialized into ordinary JSON.
    payload = {}
    for name, mask in [('artery_mask', artery), ('stenosis_mask', stenosis)]:
        stream = BytesIO()
        Image.fromarray(mask.astype('uint8') * 255).save(stream, format='PNG')
        payload[name] = stream.getvalue()
    stream = BytesIO()
    np.savez_compressed(stream, artery=artery_p, stenosis=stenosis_p)
    payload['raw_scores'] = stream.getvalue()
    scores['_artifacts'] = payload
    return (overlay_png(path, artery, stenosis), int(artery.sum()), int(stenosis.sum()), geometry,
            None, heatmap_overlay_png(path, artery_p), heatmap_overlay_png(path, stenosis_p), None,
            scores, centerline_overlay_png(path, geometry['centerline_paths'], geometry['branch_points'],
                                          geometry['endpoint_points'], artery, 512))

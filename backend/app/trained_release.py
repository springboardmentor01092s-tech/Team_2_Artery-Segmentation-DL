"""Hash-pinned preserved training artifacts for the existing mask-analysis contract."""
import hashlib
import importlib.util
import json
import os
from functools import lru_cache
from pathlib import Path
import threading

from .xai_methods import gradcam_plus_plus_weights, gradcam_weights, weighted_cam

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


def current_research_evidence():
    from .task_models import catalog
    evidence=json.loads((ROOT/'ml/releases/research_evidence_20261023.json').read_text())
    connections={row['id']:row for row in catalog()}
    for row in evidence['tasks']:
        connection=connections.get(row['task_id'])
        if connection:
            row['inference_connected']=connection['connected']
            row['connection_state']=connection['state']
    evidence['limitations']=[text for text in evidence.get('limitations',[]) if not text.startswith('Only the two listed')]
    evidence['limitations'].append('Connection status is the current hash-verified research adapter registry; historical metrics remain unchanged. Connected does not mean clinically validated or newly improved.')
    return evidence


def status():
    return dict(version=RELEASE['version'], configured=configured(), ready=ready() if configured() else False,
                input_contract='512x512 prepared coronary X-ray; grayscale0..1 artery,RGB0..1 stenosis; no extra autocontrast or morphology',
                models=RELEASE['models'], limitations=RELEASE['limitations'], research_only=True,
                research_evidence=current_research_evidence(),
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
    if (checkpoint['architecture'] != 'maskrcnn_resnet50_fpn' or checkpoint['num_classes'] != 2
            or checkpoint.get('category_ids') != [26] or checkpoint.get('input_size') != 512):
        raise ValueError('Unexpected stenosis architecture/class map')
    stenosis = build_detector(checkpoint['architecture'], checkpoint['num_classes'], pretrained=False)
    from .legacy_detector_normalization import restore_legacy_stenosis_backbone
    restore_legacy_stenosis_backbone(stenosis)
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
        profile = next(item for item in RELEASE['models'] if item['task'] == 'stenosis')
        instances = predict_one(stenosis_model, torch.from_numpy(color.transpose(2, 0, 1).copy()), 'cpu', profile['score_threshold'])
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


def _detector_explanations(model, image, score_threshold, candidate_position=None, extras=None):
    """Return frozen-detector Grad-CAM and FPN activation energy in input coordinates.

    Mask R-CNN has no attention gates.  The second map is therefore explicitly an
    activation-energy view, not an attention weight or a substitute for Grad-CAM.
    """
    import torch
    import torch.nn.functional as F

    layer = model.backbone.body.layer4
    captured = {}

    def capture(_module, _inputs, output):
        captured['activation'] = output
        output.register_hook(lambda gradient: captured.__setitem__('gradient', gradient))

    handle = layer.register_forward_hook(capture)
    try:
        model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            output = model([image.detach().clone().requires_grad_(True)])[0]
            scores = output['scores']
            labels = output['labels']
            retained = torch.where((labels == 1) & (scores >= float(score_threshold)))[0]
            if candidate_position is not None:
                if type(candidate_position) is not int or not 0 <= candidate_position < retained.numel():
                    raise ValueError('Candidate position is outside the retained detector targets')
                retained = retained[candidate_position:candidate_position + 1]
        activation = captured.get('activation')
        if activation is None:
            return None, None
        activation_energy = activation.detach().square().mean(dim=1, keepdim=True).sqrt()

        def resize_normalize(value):
            value = F.interpolate(value, size=tuple(image.shape[-2:]), mode='bilinear',
                                  align_corners=False)[0, 0]
            value = value - value.min()
            return value / value.max().clamp_min(1e-8)

        activation_map = resize_normalize(activation_energy).detach().cpu().numpy()
        if retained.numel() == 0:
            return None, activation_map

        # Detection Grad-CAM is computed per retained instance.  Each candidate's
        # coarse backbone attribution is constrained by that same predicted mask
        # before candidates are combined.  This prevents the highest-score box
        # from visually displacing the other saved candidate explanations.
        instance_cams = []
        for position, index in enumerate(retained.tolist()):
            model.zero_grad(set_to_none=True)
            captured.pop('gradient', None)
            scores[index].backward(retain_graph=position < retained.numel() - 1)
            gradient = captured.get('gradient')
            if gradient is None:
                continue
            weights = gradcam_weights(gradient)
            candidate_cam = resize_normalize(weighted_cam(activation, weights))
            if extras is not None:
                candidate_cam_pp = resize_normalize(weighted_cam(activation, gradcam_plus_plus_weights(activation, gradient)))
            candidate_mask = output['masks'][index:index + 1]
            candidate_mask = F.interpolate(candidate_mask, size=tuple(image.shape[-2:]), mode='bilinear',
                                           align_corners=False)[0, 0].detach().clamp(0, 1)
            # Use the same 0.5 instance-mask operating point as the displayed
            # stenosis result so attribution cannot appear at a different site.
            instance_cams.append(candidate_cam * (candidate_mask >= 0.5))
            if extras is not None:
                extras.setdefault('_pp', []).append(candidate_cam_pp * (candidate_mask >= 0.5))
        if not instance_cams:
            return None, activation_map
        gradcam = torch.stack(instance_cams).amax(dim=0)
        gradcam = gradcam / gradcam.max().clamp_min(1e-8)
        if extras is not None and extras.get('_pp'):
            gradcam_pp = torch.stack(extras.pop('_pp')).amax(dim=0)
            extras['gradcam_plus_plus'] = (gradcam_pp / gradcam_pp.max().clamp_min(1e-8)).detach().cpu().numpy()

        return gradcam.detach().cpu().numpy(), activation_map
    finally:
        handle.remove()
        model.zero_grad(set_to_none=True)


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
    gradcam_map = activation_map = gradcam_pp_map = None
    try:
        import torch
        with Image.open(path) as opened:
            color = np.asarray(opened.convert('RGB'), dtype=np.float32).copy() / 255.
        profile = next(item for item in RELEASE['models'] if item['task'] == 'stenosis')
        with LOCK:
            _, stenosis_model = _models(str(artifact_root()))
            explanation_extras = {}
            gradcam_map, activation_map = _detector_explanations(
                stenosis_model, torch.from_numpy(color.transpose(2, 0, 1).copy()),
                profile['score_threshold'], extras=explanation_extras)
            gradcam_pp_map = explanation_extras.get('gradcam_plus_plus')
    except (RuntimeError, AttributeError, ValueError):
        # Prediction remains usable if an installed Torch/Torchvision build cannot
        # supply the required detector gradients.  The result records the absence.
        gradcam_map = activation_map = gradcam_pp_map = None
    scores = dict(artery_foreground_mean_probability=float(artery_p[artery].mean()) if artery.any() else None,
                  stenosis_foreground_mean_probability=float(stenosis_p[stenosis].mean()) if stenosis.any() else None,
                  calibration='uncalibrated_raw_pixel_and_instance_scores', instance_detections=instances,
                  trained_release=RELEASE['version'], checkpoint_sha256={x['task']: x['sha256'] for x in RELEASE['models']},
                  preprocessing='Preserved512contract; no median/autocontrast/postprocessing added',
                  absence_interpretation='No detections do not establish absence of disease',
                  operating_point={
                      'profile': RELEASE['version'],
                      'stenosis_score_threshold': next(item['score_threshold'] for item in RELEASE['models'] if item['task'] == 'stenosis'),
                      'stenosis_mask_threshold': next(item['mask_threshold'] for item in RELEASE['models'] if item['task'] == 'stenosis'),
                      'scope': 'Preserved application profile; separate from frozen research comparisons.'},
                  explainability={
                      'gradcam': ({'status': 'saved', 'method': 'instance_mask_constrained_detector_gradcam_v2',
                                   'target': 'each retained foreground detection score, combined after predicted-instance-mask constraint',
                                   'layer': 'backbone.body.layer4', 'coordinate_frame': 'prepared_512_xy',
                                   'candidate_scope': 'all retained stenosis instances at the saved operating point',
                                   'weights_updated': False, 'faithfulness_validated': False,
                                   'clinical_validated': False}
                                  if gradcam_map is not None else
                                  {'status': 'unavailable', 'reason': 'Detector gradients were not produced for a foreground target.', 'faithfulness_validated': False}),
                      'gradcam_plus_plus': ({'status': 'saved', 'method': 'instance_mask_constrained_detector_gradcam_plus_plus_v1',
                                             'target': 'each retained foreground detection score, combined after predicted-instance-mask constraint',
                                             'layer': 'backbone.body.layer4', 'coordinate_frame': 'prepared_512_xy',
                                             'weights_updated': False, 'faithfulness_validated': False,
                                             'clinical_validated': False}
                                            if gradcam_pp_map is not None else
                                            {'status': 'unavailable', 'reason': 'Detector gradients were not produced for a foreground target.', 'faithfulness_validated': False}),
                      'attention': ({'status': 'saved', 'method': 'fpn_backbone_activation_energy_v1',
                                     'label': 'Feature activation',
                                     'layer': 'backbone.body.layer4', 'coordinate_frame': 'prepared_512_xy',
                                     'attention_gate': False, 'faithfulness_validated': False,
                                     'clinical_validated': False}
                                    if activation_map is not None else
                                    {'status': 'unavailable', 'reason': 'Detector feature activations were not captured.', 'faithfulness_validated': False})})
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
    if gradcam_pp_map is not None:
        scores['_explanation_maps'] = {'gradcam_plus_plus': heatmap_overlay_png(path, gradcam_pp_map, 'attention')}
    return (overlay_png(path, artery, stenosis), int(artery.sum()), int(stenosis.sum()), geometry,
            heatmap_overlay_png(path, activation_map, 'attention') if activation_map is not None else None,
            heatmap_overlay_png(path, artery_p), heatmap_overlay_png(path, stenosis_p),
            heatmap_overlay_png(path, gradcam_map, 'attention') if gradcam_map is not None else None,
            scores, centerline_overlay_png(path, geometry['centerline_paths'], geometry['branch_points'],
                                          geometry['endpoint_points'], artery, 512))

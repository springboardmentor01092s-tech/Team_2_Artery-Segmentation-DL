#!/usr/bin/env python3
"""Checkpoint-bound, forward-only detector XAI diagnostic; never trains weights."""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.stats import spearmanr
import torch

from app import trained_release
from app.xai_faithfulness import evaluate_forward_occlusion, matched_instance_index, matched_instance_score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate-position', type=int, default=0)
    parser.add_argument('--grid', type=int, default=4)
    args = parser.parse_args()

    color = np.asarray(Image.open(args.image).convert('RGB'), dtype=np.float32) / 255
    chw = color.transpose(2, 0, 1).copy()
    image = torch.from_numpy(chw)
    _, model = trained_release._models(str(trained_release.artifact_root()))
    profile = next(item for item in trained_release.RELEASE['models'] if item['task'] == 'stenosis')
    threshold = float(profile['score_threshold'])
    with torch.inference_mode():
        original = model([image])[0]
    retained = torch.where((original['labels'] == 1) & (original['scores'] >= threshold))[0]
    if not 0 <= args.candidate_position < retained.numel():
        raise RuntimeError('Requested retained candidate is unavailable')
    target_index = int(retained[args.candidate_position])
    reference_mask = (original['masks'][target_index, 0] >= .5).detach().cpu().numpy()
    cam, _ = trained_release._detector_explanations(
        model, image, threshold, candidate_position=args.candidate_position)
    if cam is None:
        raise RuntimeError('Frozen detector did not produce the requested attribution')

    def score(target):
        def evaluate(values):
            tensor = torch.from_numpy(np.asarray(values, dtype=np.float32).copy())
            with torch.inference_mode():
                output = target([tensor])[0]
            return matched_instance_score(output, reference_mask)
        return evaluate

    baseline = np.median(chw, axis=(1, 2), keepdims=True).astype(np.float32)
    result = evaluate_forward_occlusion(
        chw, cam, score(model), grid=args.grid, seed=20261117, baseline_value=baseline)
    result['target_binding'] = 'candidate_position_and_original_instance_mask_iou'
    result['candidate_position'] = args.candidate_position
    result['original_target_score'] = float(original['scores'][target_index])
    result['baseline'] = {'method': 'per_channel_input_median', 'values': baseline.ravel().tolist()}

    randomized = copy.deepcopy(model).eval()
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(20261117)
        for module in randomized.backbone.body.layer4.modules():
            if hasattr(module, 'reset_parameters'):
                module.reset_parameters()
    with torch.inference_mode():
        random_output = randomized([image])[0]
    matched = matched_instance_index(random_output, reference_mask, minimum_score=threshold)
    random_cam = None
    if matched is not None:
        eligible = torch.where((random_output['labels'] == 1) & (random_output['scores'] >= threshold))[0]
        position = int(torch.where(eligible == matched)[0].item())
        random_cam, _ = trained_release._detector_explanations(
            randomized, image, threshold, candidate_position=position)
    if random_cam is None:
        result['randomization'] = {
            'status': 'target_unavailable_after_backbone_randomization',
            'eligible_target': False,
            'disposable_model_score': score(randomized)(chw),
        }
        result['gates']['randomization'] = False
    else:
        correlation = float(spearmanr(cam.ravel(), random_cam.ravel()).statistic)
        result['randomization'] = {
            'status': 'executed_on_disposable_model_copy',
            'eligible_target': True,
            'absolute_spearman': abs(correlation),
            'disposable_model_score': score(randomized)(chw),
        }
        result['gates']['randomization'] = (
            result['randomization']['absolute_spearman'] <=
            result['protocol']['randomized_attribution_abs_spearman_max'])
    result['status'] = ('faithfulness_controls_passed' if all(result['gates'].values())
                        else 'faithfulness_not_established')
    result.update(checkpoint_sha256=profile['sha256'],
                  model_version=trained_release.RELEASE['version'],
                  attribution_method='candidate_mask_constrained_detector_gradcam_v2',
                  coordinate_frame='prepared_512_xy', weights_updated=False)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()

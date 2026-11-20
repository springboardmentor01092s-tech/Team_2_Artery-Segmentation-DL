import numpy as np
import pytest

from app.xai_faithfulness import evaluate_forward_occlusion, matched_instance_index, matched_instance_score


def test_forward_occlusion_rewards_the_true_target_and_randomization_control():
    image = np.zeros((32, 32), dtype=np.float32)
    image[:8, :8] = 1
    attribution = np.zeros_like(image)
    attribution[:8, :8] = 1

    def score(values):
        return float(values[:8, :8].mean())

    randomized = np.random.default_rng(42).normal(size=image.shape).astype(np.float32)
    result = evaluate_forward_occlusion(
        image, attribution, score,
        randomized_score_fn=lambda values: float(values.mean()),
        randomized_attribution=randomized,
        grid=4,
    )
    assert result['status'] == 'faithfulness_controls_passed'
    assert result['gates'] == {'deletion': True, 'insertion': True, 'randomization': True}
    assert result['clinical_validated'] is False


def test_uninformative_attribution_does_not_establish_faithfulness():
    image = np.ones((16, 16), dtype=np.float32)
    attribution = np.ones_like(image)
    result = evaluate_forward_occlusion(image, attribution, lambda values: float(values.mean()), grid=4)
    assert result['status'] == 'faithfulness_not_established'
    assert result['gates']['randomization'] is False


def test_geometry_and_partial_randomization_controls_are_rejected():
    with pytest.raises(ValueError, match='exact input'):
        evaluate_forward_occlusion(np.ones((16, 16)), np.ones((8, 8)), lambda values: 1, grid=4)
    with pytest.raises(ValueError, match='together'):
        evaluate_forward_occlusion(np.ones((16, 16)), np.ones((16, 16)), lambda values: 1,
                                   randomized_score_fn=lambda values: 0, grid=4)


def test_detection_target_is_bound_by_mask_iou():
    import torch

    reference = np.zeros((8, 8), dtype=bool)
    reference[:3, :3] = True
    masks = torch.zeros((2, 1, 8, 8))
    masks[0, 0, 5:, 5:] = 1
    masks[1, 0, :3, :3] = 1
    output = {'labels': torch.tensor([1, 1]), 'scores': torch.tensor([.99, .61]), 'masks': masks}
    assert matched_instance_score(output, reference) == pytest.approx(.61)
    assert matched_instance_index(output, reference, minimum_score=.60) is not None
    assert matched_instance_index(output, reference, minimum_score=.70) is None
    assert matched_instance_score(output, np.eye(8, dtype=bool), minimum_iou=.9) == 0


def test_channel_baseline_is_broadcast_and_invalid_shape_rejected():
    image = np.ones((3, 16, 16), dtype=np.float32)
    attribution = np.zeros((16, 16), dtype=np.float32)
    attribution[:4, :4] = 1
    result = evaluate_forward_occlusion(
        image, attribution, lambda value: float(value[:, :4, :4].mean()),
        baseline_value=np.array([.2, .3, .4], dtype=np.float32)[:, None, None], grid=4)
    assert np.isfinite(list(result['metrics'].values())).all()
    with pytest.raises(ValueError, match='Baseline'):
        evaluate_forward_occlusion(image, attribution, lambda value: 0,
                                   baseline_value=np.ones((2, 2)), grid=4)

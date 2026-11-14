import numpy as np
import pytest

from app.xai_faithfulness import evaluate_forward_occlusion


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

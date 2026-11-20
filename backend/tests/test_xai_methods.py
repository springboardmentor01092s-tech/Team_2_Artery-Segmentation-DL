import pytest

torch = pytest.importorskip("torch")

from app.xai_methods import gradcam_plus_plus_weights, gradcam_weights, weighted_cam


def test_gradcam_and_plus_plus_highlight_the_responsible_channel():
    activation = torch.zeros(1, 2, 8, 8)
    activation[0, 0, 2:4, 2:4] = 1.0   # channel 0 fires at a small region
    activation[0, 1] = 0.2              # channel 1 is diffuse
    gradient = torch.zeros_like(activation)
    gradient[0, 0] = 1.0                # target depends on channel 0 only
    for weights in (gradcam_weights(gradient), gradcam_plus_plus_weights(activation, gradient)):
        cam = weighted_cam(activation, weights)[0, 0]
        assert cam[2:4, 2:4].min() > 0
        assert cam[6, 6] == 0


def test_plus_plus_ignores_negative_gradients_and_is_finite():
    activation = torch.rand(1, 3, 5, 5)
    gradient = -torch.rand(1, 3, 5, 5)
    weights = gradcam_plus_plus_weights(activation, gradient)
    assert torch.isfinite(weights).all()
    assert (weights == 0).all()

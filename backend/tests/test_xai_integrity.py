"""Method-specific attribution integrity checks; synthetic inputs only."""
import hashlib

import pytest


def _state_hash(model):
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def test_gradcam_preserves_model_state_and_exact_input_frame():
    torch = pytest.importorskip("torch")
    from app.analysis_model import build_model
    from app.analysis_service import _gradcam

    model = build_model().eval()
    image = torch.zeros((1, 1, 160, 192), dtype=torch.float32)
    before = _state_hash(model)
    training_before = model.training

    attribution = _gradcam(model, image, 0.5)

    assert attribution.shape == (160, 192)
    assert _state_hash(model) == before
    assert model.training is training_before is False
    assert all(parameter.grad is None for parameter in model.parameters())
    assert len(model.middle._forward_hooks) == 0


def test_saved_result_fails_closed_without_xai_provenance():
    from types import SimpleNamespace
    from app.analysis_result import build_result

    image = SimpleNamespace(id="image", width=512, height=512,
        source_sha256="source", processed_sha256="prepared",
        preprocessing_config_json='{"modality":"XCA"}')
    case = SimpleNamespace(id="case", modality="XCA", anatomy="coronary")
    result = build_result(event_id="event", job_id=None, image=image, case=case,
        version="synthetic", scores={}, vessel={}, artery_pixels=0,
        stenosis_pixels=0, evidence={}, artifacts={}, timestamp="2026-10-29T00:00:00Z")
    assert result["models"]["explainability"]["gradcam"]["status"] == "unavailable"
    assert result["models"]["explainability"]["attention"]["status"] == "unavailable"

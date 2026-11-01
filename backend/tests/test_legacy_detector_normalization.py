"""Synthetic two-channel software checks, no trained model or medical data."""
import pytest
import torch
from torch import nn
from torchvision.ops.misc import FrozenBatchNorm2d
from app.legacy_detector_normalization import restore_legacy_stenosis_backbone


def test_restore_before_strict_checkpoint_loading_and_numeric_contract():
    model = nn.Module()
    model.backbone = nn.Sequential(nn.BatchNorm2d(2), nn.Sequential(nn.BatchNorm2d(2)))
    model.head = nn.BatchNorm2d(2)
    expected = nn.Module()
    expected.backbone = nn.Sequential(FrozenBatchNorm2d(2, eps=0.0), nn.Sequential(FrozenBatchNorm2d(2, eps=0.0)))
    expected.head = nn.BatchNorm2d(2)
    expected.backbone[0].weight.copy_(torch.tensor([2.,3.]))
    expected.backbone[0].running_var.copy_(torch.tensor([4.,9.]))
    payload = expected.state_dict()
    result = restore_legacy_stenosis_backbone(model)
    model.load_state_dict(payload, strict=True)
    assert result['replaced_layers'] == ['backbone.0', 'backbone.1.0']
    assert model.head.__class__ is nn.BatchNorm2d
    assert all(layer.eps == 0.0 for layer in model.backbone.modules() if isinstance(layer, FrozenBatchNorm2d))
    value = torch.ones((1,2,2,2))
    assert torch.equal(model.backbone(value), expected.backbone(value))
    assert not any(parameter.requires_grad for parameter in model.backbone.parameters())


def test_already_restored_backbone_is_idempotent():
    model = nn.Module()
    model.backbone = nn.Sequential(FrozenBatchNorm2d(2,eps=0.00001))
    assert restore_legacy_stenosis_backbone(model)['replaced_layers'] == []
    assert model.backbone[0].eps == 0.0


def test_unknown_backbone_contract_fails_closed():
    model = nn.Module()
    with pytest.raises(ValueError,match='backbone missing'):
        restore_legacy_stenosis_backbone(model)
    model.backbone = nn.Sequential(nn.Conv2d(1,2,1))
    with pytest.raises(ValueError,match='Expected legacy'):
        restore_legacy_stenosis_backbone(model)

"""Restore the known COCO-v1 training factory contract before strict weight load.

This helper is for the hash-pinned legacy stenosis release only. Its source-backed
normalization reconstruction reproduced exact baseline parity on Kaggle run
364196526. It does not improve, retrain or activate checkpoint weights.
"""


def restore_legacy_stenosis_backbone(model):
    import torch
    from torchvision.ops.misc import FrozenBatchNorm2d

    changed = []

    def restore(parent, prefix):
        for name, layer in list(parent.named_children()):
            path = prefix + '.' + name
            if isinstance(layer, torch.nn.BatchNorm2d):
                if layer.running_mean is None or layer.running_var is None:
                    raise ValueError('Legacy backbone normalization requires running statistics')
                replacement = FrozenBatchNorm2d(layer.num_features, eps=0.0).to(
                    device=layer.running_mean.device, dtype=layer.running_mean.dtype)
                setattr(parent, name, replacement)
                changed.append(path)
            elif isinstance(layer, FrozenBatchNorm2d):
                layer.eps = 0.0
            else:
                restore(layer, path)

    if not hasattr(model, 'backbone'):
        raise ValueError('Legacy detector backbone missing')
    restore(model.backbone, 'backbone')
    if not any(isinstance(layer, FrozenBatchNorm2d) for layer in model.backbone.modules()):
        raise ValueError('Expected legacy backbone normalization layers')
    return {'contract': 'legacy_coco_v1_frozen_batchnorm_eps0',
            'replaced_layers': changed, 'checkpoint_weights_changed': False,
            'parity_evidence_run_id': 364196526}

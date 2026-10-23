"""One-shot held-out evaluation of a frozen CADICA validation-selected model."""
import argparse
import hashlib
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from train_cadica_detector import Frames, collate


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--experiment',type=Path,default=Path('models/individual/cadica'))
    args=parser.parse_args()
    experiment=args.experiment if args.experiment.is_absolute() else args.root/args.experiment
    output=experiment/'final_test_report.json'
    if output.exists():
        raise FileExistsError('Final test already evaluated; do not tune on the held-out set')
    summary=json.loads((experiment/'validation_summary.json').read_text())
    assert summary['training_complete'], 'Training has not completed'
    manifest=json.loads((experiment/'split_manifest.json').read_text())
    groups=manifest['groups']
    assert not(set(groups['train']) & set(groups['test']))
    assert not(set(groups['val']) & set(groups['test']))
    assert not manifest['cross_split_pixel_duplicates']
    checkpoint_path=experiment/'best.pt'
    # Own training artifact, produced by the project trainer; no third-party pickle.
    checkpoint=torch.load(checkpoint_path,map_location='cpu',weights_only=True)
    assert checkpoint['classes']==manifest['classes']
    from torchvision.models.detection import fasterrcnn_resnet50_fpn
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    from torchmetrics.detection.mean_ap import MeanAveragePrecision
    device='cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
    model=fasterrcnn_resnet50_fpn(weights=None,weights_backbone=None,
        min_size=checkpoint.get('input_size',800),max_size=checkpoint.get('input_size',1333))
    from torchvision.ops.misc import FrozenBatchNorm2d
    def frozen_norms(parent):
        for name,child in list(parent.named_children()):
            if isinstance(child,torch.nn.BatchNorm2d):
                setattr(parent,name,FrozenBatchNorm2d(child.num_features,eps=0.0))
            else:
                frozen_norms(child)
    frozen_norms(model.backbone.body)
    model.roi_heads.box_predictor=FastRCNNPredictor(model.roi_heads.box_predictor.cls_score.in_features,len(manifest['classes'])+1)
    model.load_state_dict(checkpoint['model']); model.to(device).eval()
    data=Frames(args.root,manifest['splits']['test'],manifest['classes'])
    metric=MeanAveragePrecision(box_format='xyxy',class_metrics=True)
    with torch.inference_mode():
        for images,targets in DataLoader(data,batch_size=1,collate_fn=collate,num_workers=0):
            predictions=model([image.to(device) for image in images])
            metric.update([{k:v.cpu() for k,v in row.items()} for row in predictions],list(targets))
    digest=hashlib.sha256()
    with checkpoint_path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''): digest.update(block)
    report={'dataset':'CADICA','checkpoint_sha256':digest.hexdigest(),
        'selected_epoch':checkpoint['epoch'],'selection_source':'validation mAP@[.50:.95]',
        'test_images':len(data),'test_patients':len(groups['test']),
        'test_used_for_fitting_or_model_selection':False,'classes':manifest['classes'],
        'metrics':{k:v.tolist() for k,v in metric.compute().items()},
        'clinical_validation':False,'device':device}
    output.write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()

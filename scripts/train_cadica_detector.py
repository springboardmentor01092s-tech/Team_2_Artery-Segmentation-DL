"""Individual CADICA Faster R-CNN experiment; source labels remain unchanged.

Requires an audited local intake report. Original release supplies no partition
in readme.txt, so experimental patient partitions are explicitly recorded.
"""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset


class Frames(Dataset):
    def __init__(self, root, rows, classes, augment=False):
        self.root, self.rows, self.classes, self.augment = root, rows, classes, augment

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        with Image.open(self.root / row['image']) as im:
            image = torch.from_numpy(np.asarray(im.convert('RGB')).copy()).permute(2,0,1).float()/255
        if self.augment:
            image = (image * random.uniform(.9,1.1) + random.uniform(-.03,.03)).clamp(0,1)
        boxes = [[b['xywh'][0], b['xywh'][1], b['xywh'][0]+b['xywh'][2],
                  b['xywh'][1]+b['xywh'][3]] for b in row['boxes']]
        target = {'boxes': torch.tensor(boxes,dtype=torch.float32).reshape(-1,4),
                  'labels': torch.tensor([self.classes[b['source_class']] for b in row['boxes']],dtype=torch.int64)}
        return image, target


def collate(batch):
    return tuple(zip(*batch))


def partition(rows, seed):
    patients = sorted({r['patient'] for r in rows})
    if len(patients) < 10:
        raise ValueError('Too few verified patient groups')
    random.Random(seed).shuffle(patients)
    n = max(1, round(.15*len(patients)))
    groups = {'test': patients[:n], 'val':patients[n:2*n], 'train':patients[2*n:]}
    return groups, {s:[r for r in rows if r['patient'] in p] for s,p in groups.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path,default=Path('models/individual/cadica'))
    parser.add_argument('--epochs',type=int,default=40)
    parser.add_argument('--patience',type=int,default=8)
    parser.add_argument('--batch-size',type=int,default=2)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--device',choices=('auto','cuda','mps'),default='auto')
    parser.add_argument('--input-size',type=int,default=512)
    parser.add_argument('--workers',type=int,default=0)
    parser.add_argument('--resume',action='store_true')
    args = parser.parse_args()
    intake = json.loads((args.root/'reports/local_training_intake.json').read_text())['datasets']['cadica']
    assert not intake['issues'], 'Resolve source audit issues first'
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    groups, splits = partition(intake['manifest'], args.seed)
    classes = {c:i+1 for i,c in enumerate(sorted(intake['classes']))}
    output = args.output if args.output.is_absolute() else args.root/args.output
    output.mkdir(parents=True,exist_ok=True)
    # Detect leakage on decoded pixels. Reject the experiment instead of silently
    # changing a held-out partition or ignoring correlated frames.
    seen, collisions = {}, []
    for split, rows in splits.items():
        for row in rows:
            with Image.open(args.root/row['image']) as im:
                arr = np.asarray(im.convert('RGB'))
                digest = hashlib.sha256(str(arr.shape).encode()+arr.tobytes()).hexdigest()
            if digest in seen and seen[digest][0] != split:
                collisions.append([seen[digest], [split,row['image']]])
            seen[digest] = [split,row['image']]
    manifest = {'seed':args.seed,'source_split':'No official partition identified locally; experimental patient split',
                'groups':groups,'classes':classes,'splits':splits,'cross_split_pixel_duplicates':collisions,
                'licence':'CC BY 4.0','licence_source':'https://data.mendeley.com/datasets/p9bpx9ctcv/5',
                'selection_metric':'validation mAP@[0.50:0.95]', 'test_used':False}
    (output/'split_manifest.json').write_text(json.dumps(manifest,indent=2))
    assert not collisions, 'Cross-split duplicates found; review manifest before training'
    print({s:len(r) for s,r in splits.items()},flush=True)
    if args.prepare_only:
        return
    device=args.device
    if device=='auto':
        device='cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'unavailable'
    assert device!='unavailable', 'No GPU available in this process'
    assert device!='cuda' or torch.cuda.is_available(), 'CUDA unavailable'
    assert device!='mps' or torch.backends.mps.is_available(), 'Apple GPU unavailable'
    assert args.input_size>=128 and args.epochs>0 and args.patience>0
    from torchvision.models.detection import fasterrcnn_resnet50_fpn, FasterRCNN_ResNet50_FPN_Weights
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    from torchmetrics.detection.mean_ap import MeanAveragePrecision
    model = fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT,
                                  min_size=args.input_size,max_size=args.input_size)
    model.roi_heads.box_predictor = FastRCNNPredictor(model.roi_heads.box_predictor.cls_score.in_features,len(classes)+1)
    model.to(device)
    loaders = {s:DataLoader(Frames(args.root,r,classes,s=='train'),batch_size=args.batch_size,
                shuffle=s=='train',num_workers=args.workers,collate_fn=collate) for s,r in splits.items() if s!='test'}
    optimizer = torch.optim.AdamW(model.parameters(),lr=1e-4,weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer,mode='max',patience=3,factor=.5)
    best, stale, history = -1.,0,[]
    start_epoch=0
    if args.resume:
        # Only an own experiment artifact is accepted here, never third-party pickle.
        saved=torch.load(output/'last.pt',map_location=device,weights_only=False)
        assert saved['classes']==classes and saved['seed']==args.seed
        assert saved.get('input_size')==args.input_size, 'Resume geometry differs'
        model.load_state_dict(saved['model']); optimizer.load_state_dict(saved['optimizer'])
        scheduler.load_state_dict(saved['scheduler']); start_epoch=saved['epoch']
        history=json.loads((output/'history.json').read_text())
        best=max(float(r['validation']['map']) for r in history)
        best_epoch=max(i for i,r in enumerate(history) if float(r['validation']['map'])==best)
        stale=len(history)-best_epoch-1
        if 'random_state' in saved:
            random.setstate(saved['random_state'])
            numpy_state=list(saved['numpy_state']); numpy_state[1]=np.asarray(numpy_state[1],dtype=np.uint32)
            np.random.set_state(tuple(numpy_state))
            torch.set_rng_state(saved['torch_rng_state'].cpu())
    elif (output/'last.pt').exists():
        raise FileExistsError('Experiment exists: use --resume or a new output directory')
    print(f'device={device}; input_size={args.input_size}; start_epoch={start_epoch}',flush=True)
    for epoch in range(start_epoch,args.epochs):
        started=time.perf_counter()
        model.train(); losses=[]
        for images, targets in loaders['train']:
            optimizer.zero_grad(set_to_none=True)
            loss = sum(model([x.to(device) for x in images],[{k:v.to(device) for k,v in t.items()} for t in targets]).values())
            if not torch.isfinite(loss):
                raise RuntimeError('Nonfinite loss; experiment stopped')
            loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),5); optimizer.step()
            losses.append(float(loss.detach()))
        model.eval(); metric=MeanAveragePrecision(box_format='xyxy',class_metrics=True)
        with torch.inference_mode():
            for images,targets in loaders['val']:
                predictions=model([x.to(device) for x in images])
                metric.update([{k:v.cpu() for k,v in p.items()} for p in predictions],list(targets))
        metrics={k:v.tolist() for k,v in metric.compute().items()}
        row={'epoch':epoch+1,'loss':float(np.mean(losses)),'validation':metrics,
             'epoch_seconds':time.perf_counter()-started,'device':device,'input_size':args.input_size}
        history.append(row); print(row,flush=True)
        score=float(metrics['map']); scheduler.step(score)
        numpy_state=np.random.get_state()
        checkpoint={'model':model.state_dict(),'optimizer':optimizer.state_dict(),
                    'scheduler':scheduler.state_dict(),'epoch':epoch+1,'classes':classes,
                    'validation':metrics,'seed':args.seed,'test_used':False,'input_size':args.input_size,
                    'device':device,'random_state':random.getstate(),
                    'numpy_state':(numpy_state[0],numpy_state[1].tolist(),*numpy_state[2:]),
                    'torch_rng_state':torch.get_rng_state()}
        torch.save(checkpoint,output/'last.pt')
        if score>best:
            best,stale=score,0; torch.save(checkpoint,output/'best.pt')
        else:
            stale+=1
        (output/'history.json').write_text(json.dumps(history,indent=2))
        if stale>=args.patience:
            break
    (output/'validation_summary.json').write_text(json.dumps({'best_validation_map':best,
        'test_evaluation':'not performed; freeze model before final test', 'training_complete':True},indent=2))


if __name__=='__main__':
    main()

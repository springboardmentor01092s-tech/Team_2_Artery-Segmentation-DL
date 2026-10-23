"""Patient-grouped box detection. Validation selects checkpoints; test stays locked."""
import argparse,json,random,time,os
from pathlib import Path
import numpy as np
from PIL import Image,ImageEnhance
import torch
from torch.utils.data import Dataset,DataLoader,WeightedRandomSampler
from collections import Counter
from torchvision.transforms.functional import to_tensor
from torchvision.models.detection import fasterrcnn_resnet50_fpn_v2,FasterRCNN_ResNet50_FPN_V2_Weights
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

class Boxes(Dataset):
    def __init__(self,rows,root,classes,augment=False,png_frames=False):self.rows,self.root,self.classes,self.augment,self.png_frames=rows,Path(root),classes,augment,png_frames
    def __len__(self):return len(self.rows)
    def __getitem__(self,index):
        row=self.rows[index]
        image_path=self.root/row['image']
        if self.png_frames:image_path=image_path.with_suffix('.png')
        with Image.open(image_path) as source:image=source.convert('RGB')
        if image.size!=(row['width'],row['height']):raise ValueError('Image geometry changed: '+row['id'])
        if self.augment:image=ImageEnhance.Contrast(ImageEnhance.Brightness(image).enhance(random.uniform(.85,1.15))).enhance(random.uniform(.85,1.15))
        target={'boxes':torch.tensor(row['boxes'],dtype=torch.float32).reshape(-1,4),'labels':torch.tensor([self.classes.index(s)+1 for s in row['labels']],dtype=torch.int64),'image_id':torch.tensor(index)}
        return to_tensor(image),target

def collate(batch):return tuple(zip(*batch))

@torch.inference_mode()
def evaluate(model,loader,device,classes,prediction_export=None):
    model.eval();images=[];annotations=[];predictions=[];annid=1
    for batch,targets in loader:
        outputs=model([image.to(device) for image in batch])
        for target,output in zip(targets,outputs):
            index=int(target['image_id']);row=loader.dataset.rows[index]
            images.append({'id':index,'width':row['width'],'height':row['height']})
            for box,label in zip(target['boxes'].tolist(),target['labels'].tolist()):
                x,y,x2,y2=box;annotations.append({'id':annid,'image_id':index,'category_id':label,'bbox':[x,y,x2-x,y2-y],'area':(x2-x)*(y2-y),'iscrowd':0});annid+=1
            for box,label,score in zip(output['boxes'].cpu().tolist(),output['labels'].cpu().tolist(),output['scores'].cpu().tolist()):
                if score<.01:continue
                x,y,x2,y2=box;predictions.append({'image_id':index,'category_id':label,'bbox':[x,y,x2-x,y2-y],'score':score})
    if prediction_export is not None:
        Path(prediction_export).write_text(json.dumps({'images':images,'annotations':annotations,'predictions':predictions,'classes':classes,'box_format':'COCO xywh in original image coordinates','prediction_floor':.01},indent=2))
    truth=COCO();truth.dataset={'images':images,'annotations':annotations,'categories':[{'id':i+1,'name':name} for i,name in enumerate(classes)],'info':{}};truth.createIndex()
    if predictions:
        detected=truth.loadRes(predictions);scorer=COCOeval(truth,detected,'bbox');scorer.evaluate();scorer.accumulate();scorer.summarize()
        scores={'map':float(scorer.stats[0]),'map50':float(scorer.stats[1]),'map75':float(scorer.stats[2]),'recall100':float(scorer.stats[8])}
        precision=scorer.eval['precision'];scores['per_grade_map']={name:float(values[values>=0].mean()) if np.any(values>=0) else None for i,name in enumerate(classes) for values in [precision[:,:,i,0,-1]]}
    else:scores={'map':0.,'map50':0.,'map75':0.,'recall100':0.,'per_grade_map':{name:0. for name in classes}}
    scores.update(images=len(images),ground_truth_boxes=len(annotations),prediction_floor=.01,task='grade-aware bounding-box detection')
    return scores

def atomic_save(value,path):
    temporary=path.with_suffix('.tmp');torch.save(value,temporary);temporary.replace(path)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--manifest',required=True);parser.add_argument('--out',required=True);parser.add_argument('--epochs',type=int,default=30);parser.add_argument('--patience',type=int,default=8);parser.add_argument('--batch',type=int,default=2);parser.add_argument('--workers',type=int,default=2);parser.add_argument('--test',action='store_true');parser.add_argument('--png-frames',action='store_true',help='Test using losslessly converted PNG files with the same stems');parser.add_argument('--image-size',type=int,default=640);parser.add_argument('--small-lesions',action='store_true');parser.add_argument('--balanced-sampling',action='store_true');parser.add_argument('--group-balanced-sampling',action='store_true');args=parser.parse_args()
    random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.set_num_threads(4)
    if not torch.cuda.is_available() and not args.test:raise RuntimeError('Training requires a CUDA GPU')
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu');out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(Path(args.manifest).read_text());classes=manifest['classes'];splits=manifest['splits']
    frozen_manifest=out/'manifest.json'
    if frozen_manifest.exists() and json.loads(frozen_manifest.read_text())!=manifest:raise ValueError('Manifest differs from the frozen training data')
    if not args.test:frozen_manifest.write_text(json.dumps(manifest,indent=2))
    config={'architecture':'fasterrcnn_resnet50_fpn_v2','classes':classes,'seed':42,'size':args.image_size,'batch':args.batch,'epochs':args.epochs,'selection':'validation COCO bounding-box mAP 0.50:0.95','test_used_for_selection':False}
    if args.small_lesions:config['small_lesions']=True
    if args.balanced_sampling:config['balanced_sampling']=True
    if args.group_balanced_sampling:config['group_balanced_sampling']=True
    if args.balanced_sampling and args.group_balanced_sampling:raise ValueError('Select one sampling strategy')
    if (out/'config.json').exists() and json.loads((out/'config.json').read_text())!=config:raise ValueError('Run configuration differs')
    (out/'config.json').write_text(json.dumps(config,indent=2))
    model=fasterrcnn_resnet50_fpn_v2(weights=None if args.test or (out/'last.pt').exists() else FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT,weights_backbone=None,min_size=args.image_size,max_size=max(1024,args.image_size),box_score_thresh=.01)
    if args.small_lesions:
        from torchvision.models.detection.anchor_utils import AnchorGenerator
        model.rpn.anchor_generator=AnchorGenerator(sizes=((16,),(32,),(64,),(128,),(256,)),aspect_ratios=((.5,1.,2.),)*5)
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    model.roi_heads.box_predictor=FastRCNNPredictor(model.roi_heads.box_predictor.cls_score.in_features,len(classes)+1);model.to(device)
    if args.test:
        if not (out/'training_finished.json').exists():raise ValueError('Finish validation selection first')
        if (out/'test_metrics.json').exists():raise ValueError('Test was already evaluated')
        model.load_state_dict(torch.load(out/'best.pt',map_location=device,weights_only=False)['model'])
        loader=DataLoader(Boxes(splits['test'],args.root,classes,png_frames=args.png_frames),batch_size=args.batch,num_workers=args.workers,collate_fn=collate)
        scores=evaluate(model,loader,device,classes,prediction_export=out/'test_predictions.json');(out/'test_metrics.json').write_text(json.dumps(scores,indent=2));print(json.dumps(scores),flush=True);return
    sampler=None
    if args.balanced_sampling:
        frequencies=Counter(label for row in splits['train'] for label in row['labels'])
        if set(frequencies)!=set(classes):raise ValueError('Every grade requires training examples')
        weights=[max([1./np.sqrt(frequencies[label]) for label in row['labels']],default=1./np.sqrt(len(splits['train']))) for row in splits['train']]
        sampler=WeightedRandomSampler(weights,num_samples=len(weights),replacement=True)
    if args.group_balanced_sampling:
        frequencies=Counter(row['group'] for row in splits['train'])
        weights=[1./frequencies[row['group']] for row in splits['train']]
        sampler=WeightedRandomSampler(weights,num_samples=len(weights),replacement=True)
    train=DataLoader(Boxes(splits['train'],args.root,classes,True),batch_size=args.batch,shuffle=sampler is None,sampler=sampler,num_workers=args.workers,collate_fn=collate)
    val=DataLoader(Boxes(splits['val'],args.root,classes),batch_size=args.batch,num_workers=args.workers,collate_fn=collate)
    optimizer=torch.optim.SGD([p for p in model.parameters() if p.requires_grad],lr=.0025,momentum=.9,weight_decay=.0005)
    scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer,mode='max',patience=3,factor=.5)
    scaler=torch.amp.GradScaler('cuda');start=1;best=-1.;stale=0
    if (out/'last.pt').exists():
        saved=torch.load(out/'last.pt',map_location=device,weights_only=False);model.load_state_dict(saved['model']);optimizer.load_state_dict(saved['optimizer']);scheduler.load_state_dict(saved['scheduler']);scaler.load_state_dict(saved['scaler']);start=saved['epoch']+1;best=saved['best'];stale=saved['stale'];random.setstate(saved['random']);np.random.set_state(saved['numpy']);torch.set_rng_state(saved['torch'].cpu());torch.cuda.set_rng_state_all([state.cpu() for state in saved['cuda']])
    for epoch in range(start,args.epochs+1):
        model.train();began=time.monotonic();total=0.
        for images,targets in train:
            images=[i.to(device) for i in images];targets=[{k:v.to(device) for k,v in t.items()} for t in targets];optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda',dtype=torch.float16):loss=sum(model(images,targets).values())
            if not torch.isfinite(loss):raise ValueError('Nonfinite training loss')
            scaler.scale(loss).backward();scaler.unscale_(optimizer);torch.nn.utils.clip_grad_norm_(model.parameters(),5.);scaler.step(optimizer);scaler.update();total+=float(loss.detach())
        scores=evaluate(model,val,device,classes);scheduler.step(scores['map']);improved=scores['map']>best
        if improved:best=scores['map'];stale=0;atomic_save({'model':model.state_dict(),'epoch':epoch,'validation':scores,'config':config},out/'best.pt')
        else:stale+=1
        row={'epoch':epoch,'loss':total/len(train),'validation':scores,'seconds':time.monotonic()-began,'lr':optimizer.param_groups[0]['lr']}
        with (out/'history.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
        atomic_save({'model':model.state_dict(),'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),'epoch':epoch,'best':best,'stale':stale,'random':random.getstate(),'numpy':np.random.get_state(),'torch':torch.get_rng_state(),'cuda':torch.cuda.get_rng_state_all()},out/'last.pt');print(json.dumps(row),flush=True)
        if stale>=args.patience:break
    (out/'training_finished.json').write_text(json.dumps({'best_validation_map':best,'test_evaluated':False},indent=2))

if __name__=='__main__':main()

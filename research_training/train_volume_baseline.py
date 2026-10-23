"""Coarse full-field 128^3 3D baseline. Scores are explicitly at prepared resolution."""
import argparse,json,random,time
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import Dataset,DataLoader

def block(a,b):return nn.Sequential(nn.Conv3d(a,b,3,padding=1,bias=False),nn.GroupNorm(4,b),nn.LeakyReLU(.1),nn.Conv3d(b,b,3,padding=1,bias=False),nn.GroupNorm(4,b),nn.LeakyReLU(.1))
class UNet3D(nn.Module):
    def __init__(self,classes,width=12):
        super().__init__();self.enc=nn.ModuleList([block(1,width),block(width,width*2),block(width*2,width*4),block(width*4,width*8)]);self.pool=nn.MaxPool3d(2);self.up=nn.ModuleList([nn.ConvTranspose3d(width*8,width*4,2,2),nn.ConvTranspose3d(width*4,width*2,2,2),nn.ConvTranspose3d(width*2,width,2,2)]);self.dec=nn.ModuleList([block(width*8,width*4),block(width*4,width*2),block(width*2,width)]);self.head=nn.Conv3d(width,classes,1)
    def forward(self,x):
        skip=[]
        for i,encoder in enumerate(self.enc):
            x=encoder(x)
            if i<3:skip.append(x);x=self.pool(x)
        for up,decoder,s in zip(self.up,self.dec,reversed(skip)):x=decoder(torch.cat([up(x),s],1))
        return self.head(x)

class Volumes(Dataset):
    def __init__(self,root,ids,augment=False):self.root,self.ids,self.augment=Path(root),ids,augment
    def __len__(self):return len(self.ids)
    def __getitem__(self,index):
        with np.load(self.root/(self.ids[index]+'.npz')) as source:x=source['image'].astype(np.float32);y=source['mask'].astype(np.int64)
        if self.augment:
            for axis in range(3):
                if random.random()<.5:x=np.flip(x,axis);y=np.flip(y,axis)
        return torch.from_numpy(x.copy())[None],torch.from_numpy(y.copy()),self.ids[index]

def loss_fn(logits,target,classes):
    probability=logits.float().softmax(1);encoded=torch.nn.functional.one_hot(target,classes).permute(0,4,1,2,3).float();axes=(0,2,3,4)
    dice=(2*(probability*encoded).sum(axes)+1e-5)/(probability.sum(axes)+encoded.sum(axes)+1e-5)
    return torch.nn.functional.cross_entropy(logits.float(),target)+1-dice[1:].mean()

@torch.inference_mode()
def evaluate(model,loader,device,classes):
    model.eval();rows=[]
    for image,target,ids in loader:
        with torch.autocast(device_type=device.type,dtype=torch.float16,enabled=device.type=='cuda'):pred=model(image.to(device)).argmax(1).cpu()
        for prediction,truth,case in zip(pred,target,ids):
            values=[]
            for label in range(1,classes):
                a=prediction==label;b=truth==label;intersection=int((a&b).sum());pa=int(a.sum());pb=int(b.sum());values.append({'class':label,'dice':(2*intersection)/(pa+pb) if pa+pb else 1.,'iou':intersection/(pa+pb-intersection) if pa+pb else 1.,'gt_present':pb>0,'pred_voxels':pa,'gt_voxels':pb})
            rows.append({'id':case,'classes':values})
    per_class={str(label):{'dice_including_empty':float(np.mean([r['classes'][label-1]['dice'] for r in rows])),'dice_gt_present':float(np.mean([r['classes'][label-1]['dice'] for r in rows if r['classes'][label-1]['gt_present']])) if any(r['classes'][label-1]['gt_present'] for r in rows) else None} for label in range(1,classes)}
    return {'mean_foreground_dice':float(np.mean([r['dice_including_empty'] for r in per_class.values()])),'per_class':per_class,'cases':rows,'resolution':[128,128,128],'note':'Coarse resized-volume baseline; not original-resolution or surface-distance metrics.'}

def save(value,path):temporary=path.with_suffix('.tmp');torch.save(value,temporary);temporary.replace(path)
def bare(model):return model.module if isinstance(model,nn.DataParallel) else model
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data',required=True);parser.add_argument('--out',required=True);parser.add_argument('--epochs',type=int,default=150);parser.add_argument('--patience',type=int,default=25);parser.add_argument('--test',action='store_true');args=parser.parse_args()
    random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.set_num_threads(4)
    if not torch.cuda.is_available() and not args.test:raise RuntimeError('CUDA required for training')
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu');root=Path(args.data);manifest=json.loads((root/'manifest.json').read_text());classes=len(manifest['labels']);splits=manifest['splits'];out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    model=UNet3D(classes).to(device);training_batch=1
    if not args.test and torch.cuda.device_count()>1:model=nn.DataParallel(model);training_batch=2
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=1e-4);scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer,mode='max',factor=.5,patience=8);scaler=torch.amp.GradScaler('cuda',enabled=device.type=='cuda');best=-1.;stale=0;start=1
    if args.test:
        if not (out/'training_finished.json').exists() or (out/'test_metrics.json').exists():raise ValueError('Test requires completed selection and cannot be repeated')
        selected=torch.load(out/'best.pt',map_location=device,weights_only=False)
        if selected['manifest']['splits']!=splits:raise ValueError('Evaluation split differs from the frozen training manifest')
        model.load_state_dict(selected['model']);metrics=evaluate(model,DataLoader(Volumes(root,splits['test']),batch_size=1,num_workers=2),device,classes);(out/'test_metrics.json').write_text(json.dumps(metrics,indent=2));return
    if (out/'last.pt').exists():
        checkpoint=torch.load(out/'last.pt',map_location=device,weights_only=False)
        if checkpoint.get('training_batch',1)!=training_batch:raise ValueError('GPU count changed the effective training batch; use a separate run')
        bare(model).load_state_dict(checkpoint['model']);optimizer.load_state_dict(checkpoint['optimizer']);scheduler.load_state_dict(checkpoint['scheduler']);scaler.load_state_dict(checkpoint['scaler']);best=checkpoint['best'];stale=checkpoint['stale'];start=checkpoint['epoch']+1;random.setstate(checkpoint['random']);np.random.set_state(checkpoint['numpy']);torch.set_rng_state(checkpoint['torch'].cpu());torch.cuda.set_rng_state_all([r.cpu() for r in checkpoint['cuda']])
    train=DataLoader(Volumes(root,splits['train'],True),batch_size=training_batch,shuffle=True,num_workers=2,pin_memory=True);val=DataLoader(Volumes(root,splits['val']),batch_size=training_batch,num_workers=2)
    for epoch in range(start,args.epochs+1):
        model.train();began=time.monotonic();total=0.
        for image,target,_ in train:
            image=image.to(device);target=target.to(device);optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda',dtype=torch.float16):loss=loss_fn(model(image),target,classes)
            if not torch.isfinite(loss):raise ValueError('Nonfinite loss')
            scaler.scale(loss).backward();scaler.unscale_(optimizer);nn.utils.clip_grad_norm_(model.parameters(),5.);scaler.step(optimizer);scaler.update();total+=float(loss.detach())
        metrics=evaluate(model,val,device,classes);score=metrics['mean_foreground_dice'];scheduler.step(score)
        if score>best:best=score;stale=0;save({'model':bare(model).state_dict(),'epoch':epoch,'validation':metrics,'manifest':manifest,'training_batch':training_batch,'gpu_count':torch.cuda.device_count()},out/'best.pt')
        else:stale+=1
        row={'epoch':epoch,'loss':total/len(train),'validation':metrics,'seconds':time.monotonic()-began,'lr':optimizer.param_groups[0]['lr']}
        with (out/'history.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
        save({'model':bare(model).state_dict(),'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),'epoch':epoch,'best':best,'stale':stale,'random':random.getstate(),'numpy':np.random.get_state(),'torch':torch.get_rng_state(),'cuda':torch.cuda.get_rng_state_all(),'training_batch':training_batch},out/'last.pt');print(json.dumps({**row,'validation':{k:v for k,v in metrics.items() if k!='cases'},'training_batch':training_batch,'gpu_count':torch.cuda.device_count()}),flush=True)
        if stale>=args.patience:break
    (out/'training_finished.json').write_text(json.dumps({'best_validation_dice':best,'test_evaluated':False,'resolution':[128]*3}))
if __name__=='__main__':main()

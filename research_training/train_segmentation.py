"""Independent binary baselines for DCA and ARCADE, with resume and locked test."""
import argparse, json, random, time, platform
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageOps
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader

class UNet(nn.Module):
    def __init__(self, width=24):
        super().__init__()
        def block(a,b):
            return nn.Sequential(nn.Conv2d(a,b,3,padding=1),nn.GroupNorm(4,b),nn.SiLU(),nn.Conv2d(b,b,3,padding=1),nn.GroupNorm(4,b),nn.SiLU())
        self.e1=block(1,width); self.e2=block(width,width*2); self.e3=block(width*2,width*4)
        self.b=block(width*4,width*8); self.d3=block(width*12,width*4); self.d2=block(width*6,width*2); self.d1=block(width*3,width)
        self.out=nn.Conv2d(width,1,1)
    def forward(self,x):
        a=self.e1(x); b=self.e2(nn.functional.max_pool2d(a,2)); c=self.e3(nn.functional.max_pool2d(b,2)); d=self.b(nn.functional.max_pool2d(c,2))
        def up(x,y): return torch.cat([nn.functional.interpolate(x,size=y.shape[-2:],mode='bilinear',align_corners=False),y],1)
        return self.out(self.d1(up(self.d2(up(self.d3(up(d,c)),b)),a)))

class Images(Dataset):
    def __init__(self,root,task,split,size):
        self.root=Path(root); self.size=size; self.augment=split=='train'; self.task=task
        if task=='dca': self.entries=json.loads((self.root/'artifacts/dca_splits.json').read_text())[split]
        else:
            base=self.root/'Dataset/2D/ARCADE'/task/split
            d=json.loads((base/'annotations'/f'{split}.json').read_text())
            if task=='syntax': keep={c['id'] for c in d['categories'] if c['name']!='stenosis'}
            else: keep={c['id'] for c in d['categories'] if c['name']=='stenosis'}
            by_id={e['id']:[] for e in d['images']}
            for a in d['annotations']:
                if a['category_id'] in keep:
                    if not isinstance(a['segmentation'],list): raise ValueError('RLE masks require an explicit decoder')
                    by_id[a['image_id']].extend(a['segmentation'])
            self.entries=[{'id':str(e['id']),'image':str(base/'images'/e['file_name']),'polygons':by_id[e['id']]} for e in d['images']]
            if split=='train':
                audit=self.root/'artifacts/dataset_audit.json'
                if not audit.exists(): raise ValueError('Run scripts/audit.py before training')
                excluded=set(json.loads(audit.read_text())['datasets']['ARCADE'][task]['exclude_train_images'])
                self.entries=[e for e in self.entries if Path(e['image']).name not in excluded]
    def __len__(self): return len(self.entries)
    def __getitem__(self,i):
        e=self.entries[i]; im=Image.open(self.root/e['image']).convert('L')
        if self.task=='dca': m=Image.open(self.root/e['mask']).convert('L').point(lambda v:255 if v>0 else 0)
        else:
            m=Image.new('L',im.size); draw=ImageDraw.Draw(m)
            for p in e['polygons']:
                if len(p)>=6: draw.polygon(list(zip(p[::2],p[1::2])),fill=255)
        im=ImageOps.pad(im,(self.size,self.size),method=Image.Resampling.BILINEAR)
        m=ImageOps.pad(m,(self.size,self.size),method=Image.Resampling.NEAREST)
        if self.augment:
            angle=random.uniform(-12,12)
            im=im.rotate(angle,resample=Image.Resampling.BILINEAR); m=m.rotate(angle,resample=Image.Resampling.NEAREST)
        x=np.asarray(im,dtype=np.float32)/255
        if self.augment: x=np.clip(x*random.uniform(.9,1.1)+random.uniform(-.04,.04),0,1)
        return torch.from_numpy(x.copy())[None],torch.from_numpy((np.asarray(m)>0).astype(np.float32))[None], e['id']

def loss(logits,y):
    p=logits.sigmoid(); axes=(1,2,3)
    dice=(2*(p*y).sum(axes)+1)/(p.sum(axes)+y.sum(axes)+1)
    return nn.functional.binary_cross_entropy_with_logits(logits,y)+1-dice.mean()

def portable(value):
    if isinstance(value,torch.Tensor): return value.detach().cpu()
    if isinstance(value,dict): return {k:portable(v) for k,v in value.items()}
    if isinstance(value,list): return [portable(v) for v in value]
    if isinstance(value,tuple): return tuple(portable(v) for v in value)
    return value

@torch.no_grad()
def evaluate(model,loader,device):
    model.eval(); rows=[]
    for x,y,ids in loader:
        p=model(x.to(device)).sigmoid().cpu()>=.5; g=y>=.5
        for i,k in enumerate(ids):
            tp=int((p[i]&g[i]).sum()); fp=int((p[i]&~g[i]).sum()); fn=int((~p[i]&g[i]).sum()); tn=int((~p[i]&~g[i]).sum())
            rows.append({'id':k,'dice':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 1.,'iou':tp/(tp+fp+fn) if tp+fp+fn else 1.,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,'specificity':tn/(tn+fp) if tn+fp else None,'tp':tp,'fp':fp,'fn':fn,'tn':tn})
    summary={k:float(np.mean([r[k] for r in rows if r[k] is not None])) if any(r[k] is not None for r in rows) else None for k in ['dice','iou','precision','recall','specificity']}
    summary['cases']=len(rows); summary['resolution']=loader.dataset.size; summary['threshold']=.5
    return summary,rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1])); ap.add_argument('--task',choices=['dca','syntax','stenosis'],required=True); ap.add_argument('--epochs',type=int,default=150); ap.add_argument('--size',type=int,default=512); ap.add_argument('--batch',type=int,default=4); ap.add_argument('--width',type=int,default=24); ap.add_argument('--lr',type=float,default=.001); ap.add_argument('--seed',type=int,default=42); ap.add_argument('--patience',type=int,default=30); ap.add_argument('--threads',type=int,default=4); ap.add_argument('--run',default='baseline'); ap.add_argument('--test',action='store_true'); ap.add_argument('--device',choices=['auto','cpu','cuda','directml'],default='auto'); args=ap.parse_args()
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed); torch.set_num_threads(args.threads)
    device='cuda' if torch.cuda.is_available() else 'cpu'
    if args.device=='directml':
        import torch_directml
        device=torch_directml.device()
        print('DirectML adapter:',torch_directml.device_name(0).replace('\x00',''),flush=True)
    elif args.device!='auto': device=args.device
    out=Path(args.root)/'experiments'/args.task/args.run; out.mkdir(parents=True,exist_ok=True)
    config=vars(args)|{'device':str(device),'torch':torch.__version__,'platform':platform.platform(),'target':'binary vessel union excluding stenosis' if args.task=='syntax' else 'binary mask','metric_scope':'resized 2D masks; not official instance detection benchmark'}
    if (out/'config.json').exists():
        old=json.loads((out/'config.json').read_text())
        for key in ['task','size','width','seed','lr','batch']:
            if old[key]!=config[key]: raise ValueError(f'Resume config mismatch: {key}; choose another run')
    (out/'config.json').write_text(json.dumps(config,indent=2))
    model=UNet(args.width).to(device); opt=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=1e-4); sched=torch.optim.lr_scheduler.ReduceLROnPlateau(opt,mode='max',patience=8,factor=.5)
    if args.test:
        if (out/'test_metrics.json').exists(): raise RuntimeError('Test already evaluated; do not tune repeatedly on test')
        checkpoint=torch.load(out/'best.pt',map_location='cpu',weights_only=False); model.load_state_dict(checkpoint['model'])
        summary,rows=evaluate(model,DataLoader(Images(args.root,args.task,'test',args.size),batch_size=args.batch),device)
        (out/'test_metrics.json').write_text(json.dumps({'summary':summary,'per_case':rows,'epoch':checkpoint['epoch']},indent=2)); print(summary); return
    train=DataLoader(Images(args.root,args.task,'train',args.size),batch_size=args.batch,shuffle=True)
    val=DataLoader(Images(args.root,args.task,'val',args.size),batch_size=args.batch)
    start=0; best=-1; stale=0
    if (out/'last.pt').exists():
        ck=torch.load(out/'last.pt',map_location='cpu',weights_only=False); model.load_state_dict(ck['model']); opt.load_state_dict(ck['optimizer']); sched.load_state_dict(ck['scheduler']); start=ck['epoch']+1; best=ck['best']; stale=ck['stale']; random.setstate(ck['python_rng']); np.random.set_state(ck['numpy_rng']); torch.set_rng_state(ck['torch_rng'])
    last_epoch=start
    for epoch in range(start,args.epochs):
        last_epoch=epoch+1
        model.train(); total=0; count=0; t=time.time()
        for x,y,_ in train:
            x=x.to(device); y=y.to(device); opt.zero_grad(set_to_none=True); l=loss(model(x),y); l.backward(); nn.utils.clip_grad_norm_(model.parameters(),5); opt.step(); total+=l.item()*len(x); count+=len(x)
        metrics,_=evaluate(model,val,device); improved=metrics['dice']>best
        if improved: best=metrics['dice']; stale=0
        else: stale+=1
        sched.step(metrics['dice'])
        ck={'model':model.state_dict(),'optimizer':opt.state_dict(),'scheduler':sched.state_dict(),'epoch':epoch,'best':best,'stale':stale,'python_rng':random.getstate(),'numpy_rng':np.random.get_state(),'torch_rng':torch.get_rng_state()}
        ck=portable(ck)
        torch.save(ck,out/'last.tmp'); (out/'last.tmp').replace(out/'last.pt')
        if improved: torch.save(ck,out/'best.pt')
        row={'epoch':epoch+1,'loss':total/count,'val':metrics,'seconds':time.time()-t,'lr':opt.param_groups[0]['lr']}
        with (out/'history.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True)
        if stale>=args.patience: break
    (out/'training_finished.json').write_text(json.dumps({'best_val_dice':best,'last_epoch':last_epoch,'test_evaluated':False}))
if __name__=='__main__': main()

"""Validation-selected ResNet34 encoder U-Net; training and validation only."""
import argparse,json,random,time
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision.models import resnet34,ResNet34_Weights
from train_segmentation import Images,loss,evaluate,portable

def block(a,b):return nn.Sequential(nn.Conv2d(a,b,3,padding=1,bias=False),nn.GroupNorm(8,b),nn.ReLU(),nn.Conv2d(b,b,3,padding=1,bias=False),nn.GroupNorm(8,b),nn.ReLU())
class PretrainedVesselUNet(nn.Module):
    def __init__(self,pretrained=False):
        super().__init__();self.encoder=resnet34(weights=ResNet34_Weights.DEFAULT if pretrained else None);self.d3=block(512+256,256);self.d2=block(256+128,128);self.d1=block(128+64,64);self.d0=block(64+64,32);self.head=nn.Conv2d(32,1,1);self.register_buffer('mean',torch.tensor([.485,.456,.406])[None,:,None,None]);self.register_buffer('std',torch.tensor([.229,.224,.225])[None,:,None,None])
    def forward(self,x):
        size=x.shape[-2:];x=(x.repeat(1,3,1,1)-self.mean)/self.std;e=self.encoder;a=e.relu(e.bn1(e.conv1(x)));b=e.layer1(e.maxpool(a));c=e.layer2(b);d=e.layer3(c);z=e.layer4(d)
        def up(x,y):return torch.cat([nn.functional.interpolate(x,size=y.shape[-2:],mode='bilinear',align_corners=False),y],1)
        z=self.d0(up(self.d1(up(self.d2(up(self.d3(up(z,d)),c)),b)),a))
        return self.head(nn.functional.interpolate(z,size=size,mode='bilinear',align_corners=False))
def save(value,path):
    temp=path.with_suffix('.tmp');torch.save(value,temp);temp.replace(path)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--task',choices=['syntax','dca'],default='syntax');ap.add_argument('--device',choices=['cuda','cpu'],default='cuda');ap.add_argument('--initial-checkpoint');args=ap.parse_args();torch.set_num_threads(2);torch.manual_seed(42);np.random.seed(42);random.seed(42)
    if args.device=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA requested but unavailable')
    device=torch.device(args.device)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);resume=(out/'last.pt').exists();model=PretrainedVesselUNet(pretrained=not resume and not args.initial_checkpoint).to(device)
    if args.initial_checkpoint and not resume:model.load_state_dict(torch.load(args.initial_checkpoint,map_location='cpu',weights_only=False)['model'])
    optimizer=torch.optim.AdamW(model.parameters(),lr=.0001,weight_decay=.0001);scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer,mode='max',factor=.5,patience=3);scaler=torch.amp.GradScaler('cuda',enabled=device.type=='cuda');best=-1.;stale=0;start=1
    config={'architecture':'ResNet34 ImageNet encoder U-Net','task':args.task+' binary vessel segmentation','size':512,'batch':2,'seed':42,'epochs':40,'patience':8,'lr':.0001,'loss':'BCE + soft Dice','selection':'Mean per-image validation binary Dice at threshold .5','test_used_for_selection':False,'normalization':'Input grayscale [0,1] repeated RGB, ImageNet channel means/std','interpolation':'PyTorch CUDA/CPU bilinear half-pixel align_corners=False','device':args.device,'initial_checkpoint':args.initial_checkpoint};(out/'config.json').write_text(json.dumps(config,indent=2))
    if resume:
        ck=torch.load(out/'last.pt',map_location='cpu',weights_only=False);model.load_state_dict(ck['model']);optimizer.load_state_dict(ck['optimizer']);scheduler.load_state_dict(ck['scheduler']);scaler.load_state_dict(ck['scaler']);start=ck['epoch']+1;best=ck['best'];stale=ck['stale'];random.setstate(ck['random']);np.random.set_state(ck['numpy']);torch.set_rng_state(ck['torch']);torch.cuda.set_rng_state_all([r.cpu() for r in ck['cuda']]) if device.type=='cuda' else None
    train=DataLoader(Images(args.root,args.task,'train',512),batch_size=2,shuffle=True,num_workers=2);val=DataLoader(Images(args.root,args.task,'val',512),batch_size=2,num_workers=2)
    for epoch in range(start,41):
        model.train();began=time.monotonic();total=0.
        for x,y,_ in train:
            x=x.to(device);y=y.to(device);optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device.type,dtype=torch.float16,enabled=device.type=='cuda'):value=loss(model(x),y)
            if not torch.isfinite(value):raise ValueError('Nonfinite loss')
            scaler.scale(value).backward();scaler.unscale_(optimizer);nn.utils.clip_grad_norm_(model.parameters(),5.);scaler.step(optimizer);scaler.update();total+=float(value.detach())
        metrics,rows=evaluate(model,val,device);scheduler.step(metrics['dice'])
        if metrics['dice']>best:best=metrics['dice'];stale=0;save({'model':portable(model.state_dict()),'epoch':epoch,'validation':metrics,'config':config},out/'best.pt');(out/'best_validation_per_case.json').write_text(json.dumps(rows,indent=2))
        else:stale+=1
        row={'epoch':epoch,'loss':total/len(train),'validation':metrics,'seconds':time.monotonic()-began,'lr':optimizer.param_groups[0]['lr']}
        with (out/'history.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        save({'model':portable(model.state_dict()),'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),'epoch':epoch,'best':best,'stale':stale,'random':random.getstate(),'numpy':np.random.get_state(),'torch':torch.get_rng_state(),'cuda':torch.cuda.get_rng_state_all() if device.type=='cuda' else []},out/'last.pt');print(json.dumps(row),flush=True)
        if stale>=8:break
    (out/'training_finished.json').write_text(json.dumps({'best_validation_dice':best,'test_evaluated':False},indent=2))
if __name__=='__main__':main()

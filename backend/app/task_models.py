"""Explicit research-only task adapters. Never changes the active release."""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[2]
SPECS={
 'arcade_artery_binary':dict(title='ARCADE artery',filename='artery.pt',sha256='ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c',kind='active_2d',dimension='2D',anatomy='coronary'),
 'arcade_stenosis':dict(title='ARCADE stenosis masks',filename='stenosis.pt',sha256='f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3',kind='active_2d',dimension='2D',anatomy='coronary'),
 'dca_vessels':dict(title='DCA vessels · preserved ResNet34 candidate',filename='dca.pt',sha256='654c99dd3e575d7c32048e64265e6237e4522271c7368283c0ff0678c91e6541',kind='vessel',dimension='2D',anatomy='coronary',threshold=.3,package='dca_binary_resnet34_v1',source='best.pt'),
 'arcade_anatomical_instances':dict(title='ARCADE anatomical instances',filename='anatomy.pt',sha256='59422bb0d02b7ea80e4279d34b48fae70aee96bfc8b35ee0f7d7237019688654',kind='instances',dimension='2D',anatomy='coronary',threshold=.75,package='syntax',source='models/candidate_02_maskrcnn_resnet50_fpn_v2/best.pt'),
 'cadica_localization':dict(title='CADICA localization · class-agnostic view',filename='cadica.pt',sha256='9c4c7d52e8fe420c88eaee88e6d49b694b9bdd7be77cd0d84dee4653ab0aff46',kind='boxes',dimension='2D',anatomy='coronary',threshold=.5,package='cadica_corrected',source='models/candidate_01_models/best.pt'),
 'cadica_grade_aware':dict(title='CADICA source-grade boxes · not clinical severity',filename='cadica.pt',sha256='9c4c7d52e8fe420c88eaee88e6d49b694b9bdd7be77cd0d84dee4653ab0aff46',kind='boxes',dimension='2D',anatomy='coronary',threshold=.5,package='cadica_corrected',source='models/candidate_01_models/best.pt'),
 'archive_lesions':dict(title='Stenosis archive lesion boxes',filename='archive.pt',sha256='57a42245560455fcec67c2b5c27cd5949041be6a85e909c62ff578d418f7bfc9',kind='boxes',dimension='2D',anatomy='coronary',threshold=.5,package='stenosis_boxes',source='models/candidate_01_models/best.pt'),
 'imagecas':dict(title='ImageCAS coronary CTA',filename='imagecas128.pt',sha256='b77271b1780f32100bc954ccbec2ac5c4efa54a10e0f5975b631924c8a2f553d',kind='volume',dimension='3D',anatomy='coronary',label='coronary_artery'),
 'imagecasx':dict(title='ImageCAS-X coronary CTA · original baseline',filename='imagecasx.pt',sha256='8a978778e2f6d36980c08656e932d5d9b8d99938e805d21c5aa9655a0953ffa4',kind='volume',dimension='3D',anatomy='coronary',label='coronary_artery',package='imagecasx128',source='models/candidate_01_models/best.pt'),
 'aorta_aligned':dict(title='AortaSeg CT · pseudo-label research baseline',filename='aorta.pt',sha256='3b0af653ed92bcc750f24ecf493f03d98e13dc5ed5036096c36172b163ed92ad',kind='volume',dimension='3D',anatomy='aorta',label='aorta',package='aorta128',source='models/candidate_01_models/best.pt'),
}


def checkpoint_path(identity):
    spec=SPECS[identity]
    if spec['kind']=='active_2d':return Path(os.getenv('COROVISION_TRAINED_RELEASE',ROOT/'models/trained_release'))/spec['filename']
    if identity=='imagecas':return Path(os.getenv('COROVISION_3D_CHECKPOINT',ROOT/'models/volume_release/imagecas128.pt'))
    return Path(os.getenv('COROVISION_TASK_MODELS',ROOT/'models/task_release'))/spec['filename']


@lru_cache(maxsize=48)
def _verified(path,size,mtime,expected):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()==expected


def installed(identity):
    try:
        path=checkpoint_path(identity);stat=path.stat()
        return _verified(str(path),stat.st_size,stat.st_mtime_ns,SPECS[identity]['sha256'])
    except OSError:return False


def catalog():
    rows=[]
    for identity,spec in SPECS.items():
        ready=installed(identity)
        rows.append(dict(id=identity,title=spec['title'],dimension=spec['dimension'],anatomy=spec['anatomy'],
            modality='CT/CTA' if identity=='aorta_aligned' else 'CTA' if spec['dimension']=='3D' else 'XCA',
            connected=ready,installed=ready,checkpoint_sha256=spec['sha256'],
            state='research_adapter_available' if ready else 'checkpoint_unavailable_or_hash_mismatch',
            workflow='existing_analysis' if spec['kind']=='active_2d' else 'volume_analysis' if spec['dimension']=='3D' else 'task_analysis',
            threshold=spec.get('threshold'),clinical_validated=False,
            limitation='Not diagnostic. Source grades are not clinical severity; no per-image accuracy without a reference. Shared CADICA weights serve two output views.' if identity.startswith('cadica') else 'Research only. No automatic activation or claim of improved accuracy.'))
    rows.extend(dict(id=identity,title=title,dimension='3D',anatomy='hepatic',modality='CT',connected=False,
        installed=False,state='excluded_by_user',workflow=None,clinical_validated=False,
        checkpoint_sha256=None,threshold=None,limitation='Excluded from the current cycle by the user.') for identity,title in [('hepatic_vessels','Hepatic vessels'),('hepatic_tumours','Hepatic tumours')])
    return rows


def build(identity,checkpoint):
    import torch
    from .preserved_models import PretrainedVesselUNet,build_detector
    spec=SPECS[identity]
    if spec['kind']=='vessel':
        if checkpoint['config']['architecture']!='ResNet34 ImageNet encoder U-Net' or checkpoint['config']['size']!=512:raise ValueError('DCA architecture contract mismatch')
        model=PretrainedVesselUNet(False);model.load_state_dict(checkpoint['model'],strict=True)
    elif spec['kind']=='instances':
        if checkpoint['architecture']!='maskrcnn_resnet50_fpn_v2' or checkpoint['num_classes']!=26 or checkpoint['input_size']!=512 or checkpoint['category_ids']!=list(range(1,26)):raise ValueError('Anatomical class mapping mismatch')
        model=build_detector(checkpoint['architecture'],26,False);model.load_state_dict(checkpoint['state_dict'],strict=True)
    elif spec['kind']=='boxes':
        from torchvision.models.detection import fasterrcnn_resnet50_fpn_v2
        from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
        from torchvision.models.detection.anchor_utils import AnchorGenerator
        config=checkpoint['config'];classes=config['classes']
        expected=['Stenosis'] if identity=='archive_lesions' else ['p0_20','p100','p20_50','p50_70','p70_90','p90_98','p99']
        if config['architecture']!='fasterrcnn_resnet50_fpn_v2' or config['size']!=640 or classes!=expected:raise ValueError('Box detector contract mismatch')
        model=fasterrcnn_resnet50_fpn_v2(weights=None,weights_backbone=None,min_size=640,max_size=1024,box_score_thresh=.01)
        if config.get('small_lesions'):
            model.rpn.anchor_generator=AnchorGenerator(sizes=((16,),(32,),(64,),(128,),(256,)),aspect_ratios=((.5,1.,2.),)*5)
        model.roi_heads.box_predictor=FastRCNNPredictor(model.roi_heads.box_predictor.cls_score.in_features,len(classes)+1)
        model.load_state_dict(checkpoint['model'],strict=True)
    else:raise ValueError('Use the task-specific original or volume workflow')
    return model.eval()


def run_image(identity,source,output):
    import numpy as np
    import torch
    from PIL import Image,ImageDraw
    spec=SPECS[identity]
    if spec['kind'] not in {'vessel','instances','boxes'} or not installed(identity):raise ValueError('Verified task checkpoint unavailable')
    began=time.monotonic();torch.set_num_threads(2)
    checkpoint=torch.load(checkpoint_path(identity),map_location='cpu',weights_only=True)
    model=build(identity,checkpoint)
    with Image.open(source) as opened:rgb=opened.convert('RGB')
    if rgb.size!=(512,512):raise ValueError('This adapter accepts only unenhanced 512-square XCA assets')
    overlay=rgb.copy();draw=ImageDraw.Draw(overlay);records=[];output.mkdir(parents=True,exist_ok=False)
    with torch.inference_mode():
        if spec['kind']=='vessel':
            gray=np.asarray(rgb.convert('L'),dtype=np.float32)/255
            probability=model(torch.from_numpy(gray.copy())[None,None]).sigmoid()[0,0].numpy()
            mask=probability>=spec['threshold'];canvas=np.asarray(rgb).copy();canvas[mask]=(canvas[mask]*.45+np.array([0,190,150])*.55).astype('uint8');overlay=Image.fromarray(canvas)
            Image.fromarray(mask.astype('uint8')*255).save(output/'mask.png')
            np.savez_compressed(output/'probability.npz',probability=probability)
            records=[dict(foreground_pixels=int(mask.sum()))]
        else:
            x=torch.from_numpy(np.asarray(rgb,dtype=np.float32).transpose(2,0,1).copy()/255)
            prediction=model([x])[0]
            for i,score in enumerate(prediction['scores'].tolist()):
                if score<spec['threshold']:continue
                label=int(prediction['labels'][i]);box=prediction['boxes'][i].tolist()
                if not np.isfinite(box+[score]).all() or not 0<=score<=1:raise ValueError('Nonfinite detector output')
                item=dict(candidate_id=f'C{len(records)+1}',source_class_id=label,raw_score=score,bbox_xyxy=box)
                if spec['kind']=='instances':
                    if not 1<=label<=25:raise ValueError('Invalid anatomy category')
                    mask=prediction['masks'][i,0].numpy()>=.5
                    name=f'instance_{len(records)+1:03d}.png';Image.fromarray(mask.astype('uint8')*255).save(output/name)
                    item.update(mask_artifact=name,mask_pixels=int(mask.sum()))
                else:
                    classes=checkpoint['config']['classes']
                    if not 1<=label<=len(classes):raise ValueError('Invalid source category')
                    item['source_class']=classes[label-1]
                    item['display_class']='lesion_candidate' if identity=='cadica_localization' else classes[label-1]
                draw.rectangle(box,outline=(235,140,40),width=2);draw.text((box[0],max(0,box[1]-12)),f"{label}: {score:.2f}",fill=(235,140,40))
                records.append(item)
    overlay.save(output/'overlay.png')
    return dict(schema_version='task-analysis-1',task_id=identity,checkpoint_sha256=spec['sha256'],checkpoint_epoch=checkpoint.get('epoch'),
        output_kind=spec['kind'],records=records,input_shape=[512,512],threshold=spec['threshold'],
        preprocessing='512-square unenhanced asset; grayscale0..1 and internal ImageNet normalization' if spec['kind']=='vessel' else 'RGB0..1; preserved torchvision detector transform; no extra morphology',
        model_config={k:v for k,v in checkpoint.get('config',{}).items() if k in {'architecture','size','classes','small_lesions'}},
        runtime_seconds=round(time.monotonic()-began,3),reference_metrics=None,clinical_validated=False,
        limitations=['Uncalibrated research predictions; candidates are not confirmed disease.','No reference annotation supplied: no accuracy, Dice or clinical severity is inferred.','This run does not activate or replace a production model.'])

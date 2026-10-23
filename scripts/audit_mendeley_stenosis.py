"""Audit source XML boxes and retain published CSV membership without extraction."""
import collections
import csv
import io
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=ROOT/'Angiographic dataset for stenosis detection/Stenosis detection.zip'
    issues=[]; classes=collections.Counter(); sizes=collections.Counter(); manifest=[]
    with zipfile.ZipFile(source) as z:
        names=set(z.namelist())
        membership={}
        for split in ('train','test'):
            for row in csv.DictReader(io.StringIO(z.read(split+'_labels.csv').decode())):
                membership.setdefault(row['filename'],set()).add(split)
        xmls=sorted(n for n in names if n.startswith('dataset/') and n.endswith('.xml'))
        for i,name in enumerate(xmls):
            try:
                root=ET.fromstring(z.read(name))
                filename=root.findtext('filename')
                image='dataset/'+filename
                with Image.open(io.BytesIO(z.read(image))) as im:
                    im.load(); width,height=im.size
                expected=(int(root.findtext('size/width')),int(root.findtext('size/height')))
                if (width,height)!=expected:
                    raise ValueError('XML/image dimensions disagree')
                boxes=[]
                for obj in root.findall('object'):
                    label=obj.findtext('name')
                    box=[int(obj.findtext('bndbox/'+key)) for key in ('xmin','ymin','xmax','ymax')]
                    x1,y1,x2,y2=box
                    if not(0<=x1<x2<=width and 0<=y1<y2<=height):
                        raise ValueError('Invalid source box')
                    classes[label]+=1; boxes.append({'source_class':label,'source_xyxy':box})
                splits=sorted(membership.get(filename,set()))
                if len(splits)!=1:
                    raise ValueError('Missing or overlapping source CSV membership')
                sizes[f'{width}x{height}']+=1
                manifest.append({'source_member':image,'source_xml':name,'source_split':splits[0],
                    'boxes':boxes,'filename_group_candidate':filename.split('_')[1]})
            except Exception as exc:
                issues.append({'source':name,'error':str(exc)})
            if (i+1)%1000==0: print(f'Audited {i+1}/{len(xmls)}',flush=True)
        groups={s:{r['filename_group_candidate'] for r in manifest if r['source_split']==s} for s in ('train','test')}
    report={'source':str(source.relative_to(ROOT)),'licence':'CC BY 4.0',
        'licence_source':'https://data.mendeley.com/datasets/ydrm75xywg/3',
        'images_checked':len(manifest),'classes':dict(classes),'dimensions':dict(sizes),'issues':issues,
        'split_frames':dict(collections.Counter(r['source_split'] for r in manifest)),
        'shared_filename_group_candidates':sorted(groups['train']&groups['test']),
        'patient_mapping_verified':False,'training_complete':False,
        'training_gate':'Verify patient mapping and source box coordinate convention; retain original CSV splits, do not frame-randomize',
        'manifest':manifest}
    path=ROOT/'reports/mendeley_stenosis_audit.json'
    path.write_text(json.dumps(report,indent=2))
    print(path,'images:',len(manifest),'issues:',len(issues),flush=True)


if __name__=='__main__':
    main()

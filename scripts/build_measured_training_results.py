"""Summarize only persisted measurements; never substitute queued jobs for results."""
import json
import stat
import zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def recover_stenosis():
    archive=Path('/Users/lingareddydhanushkumar/Downloads/corovision_stenosis_final_results.zip')
    destination=ROOT/'output/colab_runs/20261014_stenosis'
    if not archive.is_file():
        return None
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            assert (destination/member.filename).resolve().is_relative_to(destination.resolve())
            assert not stat.S_ISLNK(member.external_attr>>16)
        assert z.testzip() is None, 'Result archive failed CRC validation'
        if not(destination/'models/individual/stenosis/test_report.json').exists():
            z.extractall(destination)
    return destination/'models/individual/stenosis/test_report.json'


def main():
    stenosis=recover_stenosis()
    syntax=ROOT/'output/colab_runs/20261014_syntax/models/individual/syntax/test_report.json'
    measured={}
    if syntax.is_file():
        row=json.loads(syntax.read_text())['final_test_results']['syntax']
        measured['ARCADE syntax']={'test_images':row['test_images'],'metrics':row['metrics'],
            'report':str(syntax),'status':'training and frozen-checkpoint test evaluation complete'}
    if stenosis and stenosis.is_file():
        row=json.loads(stenosis.read_text())
        measured['ARCADE stenosis']={'test_images':row['test_images'],'metrics':row['metrics'],
            'report':str(stenosis),'status':'training and frozen-checkpoint test evaluation complete'}
    cadica=ROOT/'models/individual/cadica_mps_20261014'
    cadica_status='training submitted on Apple MPS; no completed epoch artifact yet'
    if (cadica/'history.json').is_file():
        history=json.loads((cadica/'history.json').read_text())
        cadica_status=f'{len(history)} training epochs persisted; final test evaluation pending'
    if (cadica/'final_test_report.json').is_file():
        row=json.loads((cadica/'final_test_report.json').read_text())
        measured['CADICA']={'test_images':row['test_images'],'metrics':row['metrics'],
            'report':str(cadica/'final_test_report.json'),'status':'training and frozen-checkpoint test evaluation complete'}
        cadica_status='complete; see measured results'
    msd_root=ROOT/'models/individual/msd_nnunet/Dataset008_HepaticVessel'
    for path in sorted(msd_root.glob('**/crossval_results_folds_0_1_2_3_4/summary.json')):
        summary=json.loads(path.read_text())
        cases=summary.get('metric_per_case',[])
        if len(cases)==303:
            measured['MSD HepaticVessel']={'test_images':None,'out_of_fold_volumes':303,
                'metrics':summary['foreground_mean'],'per_class_metrics':summary.get('mean',{}),
                'report':str(path),'status':'five-fold training and full-volume out-of-fold evaluation complete'}
    queue_path=ROOT/'reports/local_gpu_queue_state.json'
    queue=json.loads(queue_path.read_text()) if queue_path.exists() else {}
    report={'updated_utc':datetime.now(timezone.utc).isoformat(),'all_datasets_complete':False,
        'measured_results':measured,'cadica_status':cadica_status,'local_queue':queue,
        'unresolved':{'ICA':'Source licence, intermediate mask semantics, patient mapping',
            'DCA1':'Source reuse terms and patient mapping',
            'Mendeley':'Release-specific patient/series mapping and source partition reconciliation'},
        'important':'Local ARCADE-rule metric is not independently certified by the challenge server; no clinical validation.'}
    output=ROOT/'reports/latest_measured_training_results.json'
    output.write_text(json.dumps(report,indent=2))
    lines=['# Measured training results', '',f'Updated UTC: {report["updated_utc"]}', '',
        '**All-dataset training is not complete.** Only persisted measured results are shown below.', '',
        '| Experiment | Test images | Union Dice | Union IoU | Instance F1 (IoU .50) | Local ARCADE-style F1 |',
        '|---|---:|---:|---:|---:|---:|']
    for name,row in measured.items():
        if not name.startswith('ARCADE'):
            continue
        m=row['metrics']
        def value(key): return f'{m[key]:.4f}' if key in m else 'not applicable'
        lines.append(f'| {name} | {row["test_images"]} | {value("pixel_dice_union_mask")} | '
            f'{value("pixel_iou_union_mask")} | {value("instance_f1_iou50")} | {value("arcade_official_f1")} |')
    if 'CADICA' in measured:
        m=measured['CADICA']['metrics']
        lines+=['','## CADICA held-out detection','',
            f"mAP@[.50:.95]: {m['map']:.4f}; AP50: {m['map_50']:.4f}; AR100: {m['mar_100']:.4f}."]
    if 'MSD HepaticVessel' in measured:
        row=measured['MSD HepaticVessel']; m=row['metrics']
        lines+=['','## MSD full-volume out-of-fold segmentation','',
            f"303 out-of-fold volumes; foreground macro Dice: {m['Dice']:.4f}; IoU: {m['IoU']:.4f}.",
            'Per-class vessel and tumour measurements are retained in the linked JSON summary. '
            'These are cross-validation scores, not official unlabeled-test scores.']
    lines+=['','Union-mask scores are supplementary binary vessel/lesion scores, not anatomical-class accuracy. '
        'These are research model evaluations, not clinical validation or evidence of highest possible performance.',
        '', '## Remaining work', '',f'- CADICA: {cadica_status}.',
        f'- Local sequential queue: `{queue.get("phase","not recorded")}`. CT model training is a separate pipeline.',
        '- ICA and DCA1: source reuse/mask/grouping clarifications remain unresolved.',
        '- Mendeley: CC BY 4.0 is confirmed. Excluding source-training frames with group tokens also in test '
        'leaves just 14 frames from one token; this cannot support a defensible train/validation split. '
        'No patient identifier or source mask interpretation was invented.',
        '', '## Saved result artifacts', '']
    for name,row in measured.items():
        lines.append(f'- {name}: [{Path(row["report"]).name}](<{row["report"]}>).')
    target=ROOT/'reports/latest_measured_training_results.md'
    target.write_text('\n'.join(lines)+'\n')
    print(target)
    print(json.dumps({name:r['status'] for name,r in measured.items()},indent=2))


if __name__=='__main__':
    main()

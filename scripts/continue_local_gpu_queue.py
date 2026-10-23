"""Finish own CADICA evaluation, then separate MSD five-fold 3D training.

This is a local sequential training process, not a scheduler or cloud service.
It records failures and never claims that a submitted job has completed.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'reports/local_gpu_queue_state.json'


def status(phase, **details):
    row={'phase':phase,'updated_utc':datetime.now(timezone.utc).isoformat(),**details}
    STATE.write_text(json.dumps(row,indent=2))
    print(json.dumps(row),flush=True)


def alive(pid):
    if pid is None:
        return False
    try:
        os.kill(pid,0)
        return True
    except ProcessLookupError:
        return False


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cadica-pid',type=int,required=True)
    parser.add_argument('--preprocess-pid',type=int,default=None,
                        help='Omit when preprocessing has already completed; artifacts are checked before training')
    args=parser.parse_args()
    status('waiting_existing_jobs',cadica_pid=args.cadica_pid,msd_preprocess_pid=args.preprocess_pid,
           training_complete=False)
    start=time.monotonic()
    while alive(args.cadica_pid) or alive(args.preprocess_pid):
        if time.monotonic()-start>48*3600:
            raise TimeoutError('Existing jobs have not finished within 48 hours; inspect their logs')
        time.sleep(30)
    cadica=ROOT/'models/individual/cadica_mps_20261014'
    assert json.loads((cadica/'validation_summary.json').read_text())['training_complete']
    status('evaluating_cadica_frozen_checkpoint',training_complete=False)
    logroot=ROOT/'output/local_gpu_logs'; logroot.mkdir(parents=True,exist_ok=True)
    if not(cadica/'final_test_report.json').exists():
        with (logroot/'cadica_final_evaluation.log').open('a') as log:
            subprocess.run([sys.executable,'scripts/evaluate_cadica_checkpoint.py','--experiment',str(cadica)],
                cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    for key,path in {'nnUNet_raw':ROOT/'data/nnunet_raw',
            'nnUNet_preprocessed':ROOT/'data/nnunet_preprocessed',
            'nnUNet_results':ROOT/'models/individual/msd_nnunet',
            'MPLCONFIGDIR':ROOT/'storage/matplotlib_cache'}.items():
        os.environ[key]=str(path)
    os.environ['nnUNet_n_proc_DA']='0'
    os.environ['nnUNet_compile']='false'
    import torch
    assert torch.backends.mps.is_available(), 'MPS unavailable in queue process'
    from nnunetv2.run.run_training import get_trainer_from_args, maybe_load_checkpoint
    base=ROOT/'data/nnunet_preprocessed/Dataset008_HepaticVessel'
    plans=json.loads((base/'nnUNetPlans.json').read_text())
    folder=base/plans['configurations']['3d_fullres']['data_identifier']
    assert len(list(folder.glob('*.pkl')))==303, 'Preprocessing is incomplete: expected 303 case-property files'
    # Use the framework's complete baseline schedule, not a tiny smoke run.
    # Only checkpoint frequency is changed for recoverability on a personal Mac.
    for fold in range(5):
        status('training_msd_3d_fullres',fold=fold,folds_total=5,device='mps',training_complete=False)
        trainer=get_trainer_from_args('8','3d_fullres',fold,device=torch.device('mps'))
        trainer.save_every=1
        out=Path(trainer.output_folder)
        checkpoints=any(out.glob('checkpoint_*.pth'))
        maybe_load_checkpoint(trainer,checkpoints,False)
        with (logroot/f'msd_fold_{fold}_orchestrator.log').open('a') as log:
            log.write(f'Fold {fold}; default epochs={trainer.num_epochs}; save_every=1\n')
        if not(out/'checkpoint_final.pth').exists():
            trainer.run_training()
        if not(out/'validation/summary.json').exists():
            trainer.perform_actual_validation(True)
        del trainer
        torch.mps.empty_cache()
    status('selecting_msd_cross_validation_configuration',training_complete=False)
    with (logroot/'msd_configuration_selection.log').open('a') as log:
        subprocess.run([str(ROOT/'backend/.venv/bin/nnUNetv2_find_best_configuration'),
            '8','-c','3d_fullres'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    status('eligible_local_jobs_completed',training_complete=True,
        unresolved_datasets=['ICA licence/masks/groups','DCA1 reuse terms/groups','Mendeley release-specific grouping'])


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        status('failed_requires_review',training_complete=False,error=f'{type(exc).__name__}: {exc}')
        raise

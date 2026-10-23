"""Generate a separate 3D CT workflow, not a claim of completed training."""
import base64
import io
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in ['scripts/audit_msd_volumes.py','scripts/prepare_msd_nnunet.py']:
            archive.write(ROOT/name,name)
    payload=base64.b64encode(buffer.getvalue()).decode()
    cells=[]
    def add(kind,text):
        row={'cell_type':kind,'metadata':{},'source':text.splitlines(True)}
        if kind=='code': row.update(execution_count=None,outputs=[])
        cells.append(row)
    add('markdown','# MSD Task08 HepaticVessel — independent 3D CT training\n'
        'Upload your existing `Task08_HepaticVessel.tar` into `/content/` using Colab Files. '
        'A GPU and substantial disk space are required. Original train/test membership, NIfTI headers '
        'and labels 0=background, 1=vessel, 2=tumour are retained. No X-ray data is used. '
        'CC BY-SA 4.0; cite Medical Segmentation Decathlon. '
        'All five full-resolution folds may exceed one free Colab session. Persist/export checkpoints '
        'before session expiry. This is a prepared workflow, not completed training.\n'
        'nnU-Net: https://github.com/MIC-DKFZ/nnUNet')
    add('code',"import base64,io,zipfile,pathlib,subprocess,sys,os,tarfile\n"
        "PROJECT=pathlib.Path('/content/msd_individual'); PROJECT.mkdir(exist_ok=True)\n"
        f"with zipfile.ZipFile(io.BytesIO(base64.b64decode({payload!r}))) as z: z.extractall(PROJECT)\n"
        "subprocess.run([sys.executable,'-m','pip','install','-q','nnunetv2','nibabel'],check=True)\n"
        "import torch\nassert torch.cuda.is_available(), 'Select GPU runtime'\n"
        "for key,folder in [('nnUNet_raw','raw'),('nnUNet_preprocessed','preprocessed'),('nnUNet_results','results')]:\n"
        "    os.environ[key]=str(PROJECT/folder); (PROJECT/folder).mkdir(exist_ok=True)\n")
    add('code',"archive=pathlib.Path('/content/Task08_HepaticVessel.tar')\n"
        "assert archive.is_file(), 'Upload the original tar archive first'\n"
        "with tarfile.open(archive) as tar:\n"
        "    tar.extractall(PROJECT,filter='data')\n"
        "(PROJECT/'reports').mkdir(exist_ok=True)\n"
        "subprocess.run([sys.executable,'scripts/audit_msd_volumes.py'],cwd=PROJECT,check=True)\n"
        "subprocess.run([sys.executable,'scripts/prepare_msd_nnunet.py','--source',str(PROJECT/'Task08_HepaticVessel'),"
        "'--audit',str(PROJECT/'reports/msd_volume_audit.json'),'--destination',os.environ['nnUNet_raw']],cwd=PROJECT,check=True)\n"
        "subprocess.run(['nnUNetv2_plan_and_preprocess','-d','8','-c','3d_fullres','--verify_dataset_integrity'],check=True)\n")
    add('code',"# Run sequentially. Retain each completed fold and its validation summary.\n"
        "for fold in range(5):\n"
        "    subprocess.run(['nnUNetv2_train','8','3d_fullres',str(fold),'--npz'],check=True)\n"
        "subprocess.run(['nnUNetv2_find_best_configuration','8','-c','3d_fullres'],check=True)\n")
    add('markdown','## Evaluation\nReport full-volume per-case and macro vessel/tumour Dice and IoU from '
        'out-of-fold predictions. Epoch patch pseudo-Dice is not final evaluation. '
        'The official test set has no local ground-truth labels, so do not invent test scores. '
        'Cross-validation selects postprocessing/ensembles; independent external validation is still required.')
    add('code',"import shutil\nfrom google.colab import files\n"
        "results=shutil.make_archive('/content/MSD_training_results','zip',PROJECT,'results')\nfiles.download(results)\n")
    target=ROOT/'colab/MSD_HepaticVessel_individual.ipynb'
    target.write_text(json.dumps({'nbformat':4,'nbformat_minor':5,'metadata':{'accelerator':'GPU',
        'kernelspec':{'name':'python3','display_name':'Python 3'}},'cells':cells},indent=2))
    print(target)


if __name__=='__main__':
    main()

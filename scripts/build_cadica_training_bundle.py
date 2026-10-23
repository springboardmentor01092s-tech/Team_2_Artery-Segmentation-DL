"""Package public selected CADICA frames, unchanged annotations and trainer."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    intake=json.loads((ROOT/'reports/local_training_intake.json').read_text())
    cadica=intake['datasets']['cadica']
    assert not cadica['issues']
    bundle=ROOT/'colab/CADICA_individual_training_bundle.zip'
    files={'scripts/train_cadica_detector.py','CADICA/readme.txt'}
    for row in cadica['manifest']:
        files.add(row['image'])
        image=Path(row['image'])
        annotation=image.parent.parent/'groundtruth'/image.with_suffix('.txt').name
        if (ROOT/annotation).exists():
            files.add(str(annotation))
    for pattern in ('p*/*Videos.txt','p*/v*/*_selectedFrames.txt'):
        files.update(str(p.relative_to(ROOT)) for p in (ROOT/'CADICA/selectedVideos').glob(pattern))
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
        for name in sorted(files):
            archive.write(ROOT/name,name)
        archive.writestr('reports/local_training_intake.json',json.dumps({'datasets':{'cadica':cadica}}))
        archive.writestr('SOURCE_AND_LICENCE.txt','CADICA authors: Jimenez-Partinen et al.\n'
            'https://data.mendeley.com/datasets/p9bpx9ctcv/5\nCC BY 4.0\n'
            'Derived package: selected source frames and source labels unchanged; clinical spreadsheet omitted.\n'
            'Patient split is experimental, not an official benchmark partition.\n')
    digest=hashlib.sha256()
    with bundle.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            digest.update(block)
    cells=[]
    def cell(kind,text):
        result={'cell_type':kind,'metadata':{},'source':text.splitlines(True)}
        if kind=='code':
            result.update(execution_count=None,outputs=[])
        cells.append(result)
    cell('markdown','# CADICA individual lesion detector\nUpload `CADICA_individual_training_bundle.zip` '
        'to the Colab Files panel at `/content/`. Select a GPU runtime. No CT or other X-ray dataset is mixed in. '
        'Source boxes/classes are preserved. Model: pretrained Faster R-CNN ResNet50 FPN. '
        'Experimental patient split, validation mAP selection, early stopping and LR reduction; test untouched. '
        'CC BY 4.0: https://data.mendeley.com/datasets/p9bpx9ctcv/5\n'
        'This notebook is prepared, not evidence of completed training. Save checkpoints before runtime expiry.')
    cell('code',"import pathlib, zipfile, hashlib, subprocess, sys\n"
        "archive=pathlib.Path('/content/CADICA_individual_training_bundle.zip')\n"
        "assert archive.is_file(), 'Upload the prepared bundle using Colab Files first'\n"
        "h=hashlib.sha256()\nwith archive.open('rb') as f:\n"
        "    for block in iter(lambda:f.read(1024*1024),b''): h.update(block)\n"
        f"assert h.hexdigest()=={digest.hexdigest()!r}, 'Bundle integrity failed'\n"
        "PROJECT=pathlib.Path('/content/cadica_individual'); PROJECT.mkdir(exist_ok=True)\n"
        "with zipfile.ZipFile(archive) as z:\n"
        "    assert z.testzip() is None\n"
        "    assert all((PROJECT/n).resolve().is_relative_to(PROJECT.resolve()) for n in z.namelist())\n"
        "    z.extractall(PROJECT)\n"
        "subprocess.run([sys.executable,'-m','pip','install','-q','torchmetrics[detection]','pycocotools'],check=True)\n"
        "import torch\nassert torch.cuda.is_available(), 'Select GPU runtime'\nprint(torch.cuda.get_device_name(0))\n")
    cell('code',"subprocess.run([sys.executable,'scripts/train_cadica_detector.py','--epochs','40',"
        "'--patience','8','--batch-size','2'],cwd=PROJECT,check=True)\n")
    cell('code',"import shutil\nfrom google.colab import files\n"
        "result=shutil.make_archive('/content/CADICA_results','zip',PROJECT,'models/individual/cadica')\nfiles.download(result)\n")
    notebook=ROOT/'colab/CADICA_individual.ipynb'
    notebook.write_text(json.dumps({'nbformat':4,'nbformat_minor':5,'metadata':{'accelerator':'GPU',
        'kernelspec':{'display_name':'Python 3','name':'python3'}},'cells':cells},indent=2))
    print(bundle, bundle.stat().st_size, digest.hexdigest(),flush=True)
    print(notebook,flush=True)


if __name__=='__main__':
    main()

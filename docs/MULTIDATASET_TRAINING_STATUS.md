# Individual dataset acquisition and training

Latest measured scores: [measured-results report](../reports/latest_measured_training_results.md).
Syntax final test evaluation is now complete (300 images, union Dice 0.7321,
local ARCADE-style task F1 0.1331). Apple MPS is available outside the sandbox:
CADICA local training is active, and MSD default 3D preprocessing is active.
A local sequential runner will evaluate CADICA and then train MSD. A user-approved
20-minute thread follow-up now checks execution and recovers final exports.
All-dataset training is **not** marked complete; source-permission/grouping gates
for ICA, DCA1 and Mendeley remain unresolved.

GPU execution recovered: see [free T4 execution update](FREE_GPU_EXECUTION_2026-10-14.md).
Syntax training completed and its checkpoint is saved locally; stenosis was
started on the existing free T4. CADICA was submitted after it, not yet verified
running. Mac locked during the final UI check; unlock required to continue.

Latest local inspection: see [14 October execution report](TRAINING_EXECUTION_2026-10-14.md).
The acquisition rows below are historical: CADICA, Mendeley, DCA1 and MSD now
have local source files. Prepared workflows are not completed GPU experiments.

Updated 2026-10-14. This is a progress record, not a claim that all training is complete.

## Project-document requirements applied

The supplied 28-page project document requires preprocessing, EDA, segmentation,
separate detection where labels support it, augmentation, checkpointing, early
stopping, and held-out evaluation. It lists candidate architectures rather than
requiring all architectures for every modality. Each dataset must first have its
actual image/annotation format and split policy verified.

## Current status

| Dataset | Official source | Current outcome | Training gate |
|---|---|---|---|
| ARCADE | https://zenodo.org/records/10390295 | Local preprocessing and EDA exist; 10 preprocessing/EDA tests pass. Separate syntax and stenosis notebooks generated. Syntax notebook imported into Colab and Run all requested on a free T4 runtime. | Full archive MD5/CRC, preprocessing and EDA must pass in Colab before training. |
| CADICA v5 | https://data.mendeley.com/datasets/p9bpx9ctcv/5 | Public archive transfer started. | Inspect actual keyframe/box files; split by patient, not frame; train a lesion detector. |
| Mendeley stenosis v3 | https://data.mendeley.com/datasets/ydrm75xywg/3 | Public archive transfer started. | Inspect supplied annotation format and patient mapping before conversion or splitting. |
| MSD Task08 HepaticVessel | https://medicaldecathlon.com/ | Public archive transfer started. | CT geometry/spacing, label dictionary, patient split and 3D data-loader verification required. Hepatic vessels are not coronary arteries. |
| TopCoW 2024 | https://zenodo.org/records/15692630 | Official public training archive transfer started. This corrects the earlier access-controlled classification. | Preserve CTA/MRA separation and paired patient groups; preserve voxel geometry and categorical labels. |
| AortaSeg-60 | https://zenodo.org/records/18147026 | Public archives resumed for EDA. | Provider README explicitly says masks should not be used as a reference standard for training new AI models; supervised training blocked pending corrected expert labels. |
| ICA | https://github.com/MIILab-MTU/ICA_NJ_BinarySeg | Download complete; CRC passed. 616 matched image/mask pairs inspected and prepared losslessly; source masks retained. 122 masks contain intermediate values. Reports and overlays generated under `data/processed/ica/`. | Resolve mask values, reuse terms and patient-level splits before training. |
| DCA1 | Author's public CIMAT archive URL | Author endpoint timed out after 60 seconds. | No data converted or training claimed. |
| ImageCAS / ImageCAS-X, ASOCA | Author/challenge access routes | No authorised dataset files available locally. | Await approved access or a verified public release with usable files. |
| TCIA | Collection-specific | No specific collection selected in supplied screenshots. | A named collection with relevant labels is required. |

## Output locations

- Raw archives: `data/raw/<dataset>/` (incomplete transfers are not processed).
- ARCADE deterministic artifacts: `data/processed/arcade/`.
- ARCADE EDA: `outputs/eda/`.
- Individual notebooks: `colab/ARCADE_syntax_individual.ipynb` and `colab/ARCADE_stenosis_individual.ipynb`.
- Notebook generator: `scripts/build_individual_colab_notebooks.py`.

Each individual notebook contains the current local scripts as an embedded ZIP,
so no GitHub upload, private repository credentials, or raw-data upload is needed.
It downloads the canonical ARCADE archive directly in Colab. It audits the test
data but trains/selects only on train/validation and exports task-specific model
results. Checkpoints remain in the runtime until exported; runtime storage is
temporary. No full training result is claimed until an epoch/checkpoint is
observed.

Live Colab notebooks (Run all requested; initial stage is data acquisition):

- Syntax: https://colab.research.google.com/drive/1Y7Wef_uZrYLuwYTW5bqjIngCBUJcXzA7
- Stenosis: https://colab.research.google.com/drive/1tVqnOGdQZVs2mVgspDuobihbJhA7BtXf

Colab allocated a T4 to syntax and reported `Torch 2.11.0+cu130 CUDA True`.
The canonical archive download is still executing, so training epochs have not
started. Starting stenosis encountered Colab's `Too many active sessions` limit;
it must run sequentially after the active task or after a session is released.
No paid runtime was requested.

The document's severity and millimetre-based measurement objectives remain
conditional on source labels and physical spacing; neither is invented for PNG
datasets.

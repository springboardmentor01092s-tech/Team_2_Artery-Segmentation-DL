# CoroVision AI dataset registry

**Last reviewed:** 2026-10-13  
**Policy:** Keep modality, anatomical region, label semantics, and evaluation protocol separate. No dataset in this registry is combined with another by copying files into a shared training folder.

| Dataset | Local status | Modality and anatomy | Verified labels | Permitted project use | Blocking condition |
|---|---|---|---|---|---|
| ARCADE | Present at `arcade/` | 2D X-ray coronary angiography | Separate SYNTAX vessel instances/categories and stenosis-region instances | Primary coronary X-ray benchmark, with separate vessel and stenosis experiments | Patient/study mapping is absent from the public files; do not claim patient-level independence or launch new controlled training until the authors reply. |
| ICA_NJ_BinarySeg v1.0 | Downloaded at `data/external/ICA_NJ_BinarySeg/` | 2D invasive coronary angiography | Binary vessel masks only | Separate vessel-mask external-audit cohort; potential external test after provenance and split policy are resolved | No declared license file or explicit patient mapping in the repository. Filename prefixes are not accepted as patient IDs. It cannot train or evaluate stenosis localization. |
| DCA1 | Not downloaded | 2D coronary angiography | Vessel masks reported by the source | Candidate external vessel dataset | Official host timed out on 2026-10-13; license, exact contents, and grouping must be verified before use. |
| ASOCA | Access request required | 3D coronary CT angiography | Coronary lumen masks | Separate 3D coronary CT segmentation project | Controlled access and dataset terms; do not mix with 2D X-ray training or ARCADE metrics. |
| ImageCAS | Not acquired | 3D coronary CT angiography | Coronary vessel segmentation reported by benchmark | Separate 3D CT project after access and licensing audit | Access and version must be verified before download. |
| AortaSeg-60 | Not acquired | 3D thoraco-abdominal CT/CTA | Automatically generated aorta masks | Separate aorta segmentation research task only | 15.9 GB download; masks are automated rather than manually corrected, and no stenosis labels are included. |
| TopCoW | Not acquired | CTA/MRA cerebral vessels | Cerebral vessel masks and graph labels | Separate brain-vessel segmentation research task only | Different anatomy/modality and license requirements; no basis for coronary stenosis claims. |
| Medical Segmentation Decathlon Task 08 | Not acquired | CT hepatic vessels | Hepatic-vessel and tumour masks | Separate hepatic-vessel segmentation research task only | Different anatomy and label semantics; no coronary or stenosis labels. |

## Training matrix

| Experiment | Input | Target | Split rule | Primary metrics |
|---|---|---|---|---|
| XCA vessel anatomy | ARCADE `syntax` | Original instance/category annotations | Official partitions remain unchanged; patient-independence unresolved | Official ARCADE instance F1, then per-class Dice/IoU |
| XCA stenosis localization | ARCADE `stenosis` | Original stenosis instances | Official partitions remain unchanged; patient-independence unresolved | Official instance F1; supplementary lesion precision/recall and Dice/IoU |
| XCA vessel generalization | ICA binary masks | Binary vessel mask | New patient-level split only if authors publish grouping metadata; otherwise descriptive audit only | Dice, IoU, precision, recall, sensitivity, specificity |
| CT coronary vessels | ASOCA or ImageCAS | Source-specific 3D vessel/lumen mask | Source-approved case-level split | Dice, HD95, connectivity and centerline coverage |
| Aorta/brain/hepatic vessels | Source-specific separate dataset | Source-specific masks | Source-approved case-level split | Source-specific segmentation metrics |

## Non-negotiable constraints

1. Train separate models for vessel segmentation and stenosis localization.
2. Do not merge 2D X-ray and 3D CT/CTA samples into one model training run.
3. Do not infer patient identity from ARCADE image IDs, ICA filename prefixes, or pixel similarity.
4. Keep the ARCADE test split locked; never tune thresholds, select models, or report a final result from it more than once.
5. Record checksum, source URL, version, date, split manifest, seed, code revision, environment, and metrics for every experiment.

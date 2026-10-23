# Dataset acquisition register

This register distinguishes resources that can be fetched without an account
from those that require a user-controlled application, login, or acceptance of
terms. Data are stored under `data/raw/<dataset>/` and are never merged across
modalities or tasks.

| Dataset | Modality / task | Access status | Action |
|---|---|---|---|
| ARCADE | 2D X-ray angiography; vessel regions and stenosis localisation | Public Zenodo, already acquired | Complete preprocessing and EDA are in this repository. |
| AortaSeg-60 | 3D CTA/CT; automated aorta masks | Public Zenodo, CC0 | Download six archives; keep source NIfTI/labels separate and validate them as a 3D task. |
| Medical Segmentation Decathlon Task08 | 3D CT; hepatic vessels/tumours | Public AWS archive | Download and retain official images/labels split metadata. |
| Mendeley angiographic stenosis dataset | 2D X-ray angiography; stenosis boxes | Public CC BY 4.0 according to NLM catalogue | Download only after its official file endpoint is verified; use a detection-specific pipeline, not ARCADE masks. |
| CADICA | 2D invasive coronary angiography; lesion annotations | Listed as open on Mendeley | Download only from the current official Mendeley record after file/license verification. |
| ImageCAS / ImageCAS-X | 3D CCTA; coronary lumen/segments/centreline | Controlled author-provided access | Request official access; do not scrape or bypass credentials. |
| ASOCA | 3D CCTA; coronary lumen | Request/account and terms required | Request access through UK Data Service or the official alternative form. |
| TopCoW 2024 | 3D CTA/MRA; Circle of Willis tasks | Account/terms or managed dataset release | Request/access through the official challenge release. |
| TCIA collections | Variable CT/CTA | Collection-specific accounts/terms | Select named collections and request/accept their conditions. |
| TopCoW winning solution | Code/methodology | Not a labelled training cohort | Do not treat as a downloadable dataset. |
| ImageCAS benchmark reference | Code/methodology | Not a separate dataset | Use only as a reproducibility reference. |

## Controlled-access request drafts

The following drafts are ready to send from the user's institutional email after
the sender account is connected. They ask only for legitimate research access.

### ImageCAS / ImageCAS-X

Subject: Research access request for ImageCAS / ImageCAS-X dataset

Hello,

I am conducting an academic project on artery segmentation and stenosis
detection using deep learning. I would like to request access to the ImageCAS
or ImageCAS-X data and associated labels for non-commercial research,
reproducibility, and model evaluation. I will follow the dataset licence,
citation requirements, and all restrictions on redistribution and patient data.

Please let me know the access procedure, applicable terms, and any required
institutional information.

Thank you.

### ASOCA

Subject: ASOCA dataset access request for academic coronary segmentation research

Hello,

I am requesting authorised access to the ASOCA CT coronary angiography dataset
for a non-commercial academic project on coronary artery segmentation. I will
use the data only under the stated terms, preserve the supplied split/evaluation
protocol, and will not redistribute the images or labels.

Please advise on the required registration, terms acceptance, and access
approval process.

Thank you.

### TopCoW 2024

Subject: TopCoW 2024 dataset access request for academic vascular segmentation

Hello,

I would like to request authorised research access to the TopCoW 2024 dataset
for a non-commercial academic project. The work concerns segmentation and
structure analysis of vascular imaging. I will comply with the dataset licence,
attribution requirements, and all rules governing data use and redistribution.

Please share the current access process and any required agreement.

Thank you.

### TCIA

TCIA access cannot be requested as a generic bulk request. A specific named
collection must first be selected because every collection has its own data-use
conditions and may not contain artery masks or stenosis labels.

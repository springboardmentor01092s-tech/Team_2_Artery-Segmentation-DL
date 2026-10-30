# Phase 2 — Model validation and limitations

Reused unchanged source audits, installed model contracts and saved Kaggle run
362745762 version 1. No fresh dataset-pixel QA or trained-model evaluation was
performed locally. Frozen ARCADE results are image-level development validation,
not independent patient or final clinical testing.

On the same 200 cases, original Dice 0.8272773138933874 versus fixed-hole candidate
0.8272789856418467 failed the predeclared >=0.001 gain. FP +62, FN -46; rejected,
baseline retained. Detailed comparison and case/cache hashes remain under the
separate research root `reports/research_live/kaggle/run_362745762_v1/`.
Comparison SHA256: c6b1c57d4e27da2ed2485b7884e6617614e18af327e2c4d7ce07acf4e96f8212.
Baseline checkpoint: ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c.

QA controls: strict preprocessing/input contracts, checkpoint hash validation,
task-specific registry and incompatible-result rejection, preserved source splits,
no anatomical-instance/binary/box equivalence and no automatic activation.

Unresolved: ARCADE patient mapping; stenosis unknown empty annotations (preserve
train 218 exclusion; do not invent healthy labels); ImageCAS/X cross-source
exposure; native-resolution/spacing validation; full source-release/license
matching; ICA mask semantics/licensing/patients. Hepatic tasks remain excluded.
CADICA source patient/video metadata offers a potential independent grouping path
but model exposure and negative annotation completeness must be checked on Kaggle.

No small-branch recovery, diameter error, calibrated disease confidence, 3D
surface performance or clinical severity result is established by fixture tests.
Model selection must keep dataset, cases, labels, aggregation and operating point
matched. Lock candidate selection before final independent testing. Do not tune
on protected tests or relabel historically exposed cases as unseen.

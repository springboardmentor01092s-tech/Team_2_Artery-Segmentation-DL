# Dataset and checkpoint exposure audit

Frozen release `ml/releases/corovision_20261023.json` records artery SHA-256 `ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c` and stenosis SHA-256 `f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3`.

ARCADE development exposure is established at cohort level. Exact patient and cross-source exposure are unresolved. CADICA and ImageCAS-X have no verified exclusion from checkpoint training and tuning. CARDIAG's [grouping receipt](../cardiag_intake_20261110/RECEIPT.json) checks overlap within its own manifests. Resolve original checkpoint manifests, preprocessing and derivative mappings, then check patient/study group overlap and exact or derived image duplicates before locking a cohort.

The [publisher index receipt](OFFICIAL_ARCHIVE_INDEX_RECEIPT.json) now binds both 200-frame ARCADE validation metadata lists to the saved mappings. One cross-split size/CRC group warrants follow-up. This does not settle the processed-mask correspondence or clearance for scoring.

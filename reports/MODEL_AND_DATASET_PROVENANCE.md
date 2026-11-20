# Model and dataset provenance — 16 November 2026

Retained SHA-256 identities: 2D artery ResNet34 U-Net `ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c`; 2D stenosis Mask R-CNN `f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3`; ImageCAS 3D checkpoint `b77271b1780f32100bc954ccbec2ac5c4efa54a10e0f5975b631924c8a2f553d`.

Registry/contracts are in `ml/releases/`, `backend/app/trained_release.py`, `preserved_models.py` and `volume_inference.py`. No checkpoint was changed or promoted. Manifest audit found ImageCAS/ImageCAS-X identity intersections across split pairings, so these variants cannot establish independent evaluation. Raw-source patient/study grouping was unavailable in this run.

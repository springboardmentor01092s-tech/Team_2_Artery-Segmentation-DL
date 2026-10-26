# End-to-end research workflow

Login → authorized case → validated upload → preview and metadata confirmation →
explicit Run analysis / queued job → pinned model input → artery segmentation →
conditional mask-derived vessel geometry + compatible image-based stenosis model →
candidate coordinate mapping → structured result and deterministic explanation →
authenticated overlays/measurements → human review and permitted export.

Inference and training remain separate. Upload does not train or silently start
analysis before metadata confirmation. AnalysisJob records pending/processing/
completed/failed; AnalysisEvent preserves prior results. Worker rechecks access,
model version and saved-input digest. New model candidates require independent
review and never auto-promote.

Current 2D detector consumes its image input, not centerline tensors. Vessel
association remains not_assessed. Severity returns insufficient_evidence without
validated candidate-local/reference measurements. Missing spacing means pixel
units, never invented millimetres. No detection does not establish a healthy case.

CT/CTA/MRA uploads remain preparation-only for inference until a compatible,
reviewed volumetric adapter/model contract is implemented and verified. Do not
silently route a volume or slice into the current 2D coronary checkpoint.

Model evaluation views use dataset/split-labelled records, never per-image
confidence claims. The explanation is generated from persisted structured fields;
no external language model independently diagnoses the upload.

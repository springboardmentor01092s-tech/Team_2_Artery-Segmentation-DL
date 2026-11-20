# Severity export evidence

Reviewed severity evidence is included in immutable research snapshots and their JSON, CSV, PDF and Evidence ZIP exports.

Each record includes case, image, analysis run, candidate, model version, reviewer identity, timestamp, MLD, RVD, unit, measurement frame, reference segment, formula, narrowing percentage, quality gate, protocol result, protocol SHA-256, calibration/measurement evidence, explanation and content SHA-256.

The PDF now prints the candidate percentage, research category or Not assessable, protocol ID/version when present, MLD/RVD and quality-gate status. CSV and JSON preserve the complete structured reviewed-measurement list. Previously saved report versions remain unchanged after later measurements or protocol changes.

Evidence ZIP browser verification is separately recorded in `EVIDENCE_ZIP_BROWSER_RECEIPT.json`; all archive hashes and report/case/image/run identifiers matched. This verifies export integrity, not severity accuracy.


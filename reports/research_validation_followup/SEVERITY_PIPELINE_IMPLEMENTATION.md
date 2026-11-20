# Severity pipeline implementation

## Implemented path

1. A saved frozen-model analysis supplies candidate IDs and original/prepared localization evidence.
2. A permitted clinical reviewer selects one persisted candidate.
3. The reviewer records minimum lumen diameter, reference vessel diameter, source frame, reference segment, calibration evidence and measurement evidence.
4. The server checks candidate/run/case identity and rejects unrelated or missing candidates.
5. Quality gates require reviewed lumen boundaries, acceptable image quality, a suitable unambiguous reference segment, compatible millimetre units, verified calibration and reviewed reference selection.
6. Diameter reduction is calculated as `100 * (RVD - MLD) / RVD`.
7. A configured eligible protocol may interpret the percentage. Without one, the category remains indeterminate.
8. The append-only record is hashed and linked to the case, image, run, candidate, model version and reviewer.
9. New reports snapshot the reviewed measurements; old reports remain immutable.

Detection, narrowing and grading remain separate values. Detector confidence is displayed only as an uncalibrated model score.

## Application integration

`Image Analysis -> Stenosis Analysis -> Severity Assessment` now exposes the candidate count, saved run, explicit no-auto-Normal behavior, lesion-specific MLD/RVD, reference segment, measurement frame, percentage reduction, quality-gate status, protocol identity and research limitation. The entry form requires two explicit quality attestations.

## Source identities

- `backend/app/stenosis_measurements.py`: SHA-256 `61e3208473f4c283017a7ce214c6ac32d2e39030df0372c64675602dd629efd3`
- `frontend/src/StenosisMeasurements.tsx`: SHA-256 `fde9147efefe2e7b7ba1849661bdb6cc940ae8b12e615dd1f6724aa76f5de329`

## Not implemented as automatic evidence

Automatic MLD/RVD extraction, automatic reference-segment selection, automatic five-class grading, case-level worst-grade aggregation and a learned severity classifier are not enabled.

The existing automatic geometry trace stops at predicted-mask centerlines and source-pixel width profiles. Its saved metadata explicitly identifies these as sampled 2D mask widths, not validated candidate-local lumen diameters. It does not select an RVD segment. The low-contrast phantom was accepted despite large error, so an automatic measurement-to-grade path remains disabled rather than bypassing the abstention requirement.


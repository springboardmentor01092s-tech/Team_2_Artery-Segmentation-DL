# Reference CSV import and lock round trip

Verified 11 November 2026 with an isolated synthetic 64 x 64 image. The test constructs two endpoint pairs measuring 10 source pixels (MLD) and 20 source pixels (RVD), converts them into the cohort schema, exports CSV, imports it against the original image, creates a new versioned snapshot and reopens it. Endpoint JSON is preserved exactly. Changing the locked CSV triggers SHA-256 rejection. Existing cohort directories cannot be overwritten.

Command from the backend directory:

```sh
.venv/bin/python -m app.reference_collection --csv /absolute/path/export.csv --images /absolute/path/original-images --output /absolute/path/new-cohort-version --version exploratory-v1
```

The importer verifies filenames, original image hashes, endpoint coordinates and widths, provenance, eligibility and blinding attestation before writing a lock. It supports source-pixel manual endpoint exports. A receipt records row count, version and CSV SHA-256. File permissions do not make these files immutable; subsequent verification detects changes to CSV bytes relative to the receipt. Preserve the receipt separately for stronger audit protection.

Executed test command:

```sh
.venv/bin/python -m pytest -q tests/test_reference_collection.py tests/test_severity_reference.py tests/test_experimental_grading.py
```

Result: 33 tests passed. This verifies the backend CSV round trip with synthetic evidence. Browser-generated downloads have not yet been passed through this round trip. No real pilot measurements were created or locked.

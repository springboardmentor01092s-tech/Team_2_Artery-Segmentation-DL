# Report and evidence consistency — 14 November 2026

Command `.git-publish/backend/.venv/bin/python scripts/verify_fresh_demo.py` completed against localhost using the existing Demo Researcher account. The script creates a new immutable 2D report snapshot and fetches its JSON, CSV, PDF and ZIP. It also fetches the fresh volume's JSON, CSV, PDF and evidence ZIP. Receipt is stored at project-root `storage/fresh_demo_proof.json`.

For the 2D ZIP, each manifest artifact was rehashed and compared with its saved SHA256, and report image identity was checked. For the 3D ZIP, every member hash was checked, manifest and analysis run IDs were compared, and geometry JSON was compared with the analysis's experimental geometry. All assertions passed. CSV/PDF responses were successful and nonempty; their rendered numerical text has not been independently re-extracted and compared in this check.

The exported 2D archive now contains available saved source/processed images, artery mask, centerline and overlay together with report formats, candidates, automatic measurement history and model provenance. Earlier reports preserve their original snapshots. Historical automatic assessments are ordered newest first.

The 3D archive includes saved mask/probability and slice previews when present, geometry with numerical cross-section sampling records, measurement CSV, report PDF and analysis JSON. Its manifest identifies pending interactive MPR/CPR and attribution. The CSV now distinguishes diameter narrowing from area narrowing and includes uncertainty status.

Browser-download and rendered PDF consistency remain pending. Protected downloads and cross-case isolation have isolated integration coverage; broader manual role/browser verification remains blocked by browser access settings.

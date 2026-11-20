# Synthetic vessel geometry results

Added a known-width vessel fixture in `backend/tests/test_width_profiles.py`. The two plateaus recovered 24 and 12 source pixels. Their width ratio gives 50% narrowing for this fixture. No model checkpoint participates in this fixture.

From `backend`:

```sh
.venv/bin/python -m pytest -q tests/test_vessel_centerline.py tests/test_width_profiles.py tests/test_geometry_candidates.py tests/test_candidate_path_association.py tests/test_saved_width_profiles.py tests/test_narrowing.py tests/test_stenosis_measurements.py tests/test_xai_integrity.py
```

74 passed with one existing TestClient deprecation warning. This tests software geometry and arithmetic on controlled inputs. Physical accuracy requires the references described in [validation status](PHYSICAL_DIAMETER_VALIDATION_STATUS.md).

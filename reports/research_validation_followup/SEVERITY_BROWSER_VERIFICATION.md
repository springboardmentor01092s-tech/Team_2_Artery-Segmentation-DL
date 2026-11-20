# Severity browser verification

## Current verification

The updated severity page compiled successfully in the production frontend build and was reopened in Chrome on 10 November 2026. The saved Case 60 context restored case `DEMO-DCA1-003-20261109`, image `dca1-003.png` and run `d0286ecd-e383-4f16-8ecb-9e662c8df223`. The page showed three persisted candidates, the run ID, the statement that no-detection is never converted to Normal, and the correct empty state: no reviewed measurements, so narrowing and severity remain unavailable. The severity component reads only persisted run/candidate measurements and contains no invented demonstration values. The full-page browser evidence is `SEVERITY_BROWSER_VERIFICATION.jpg`.

## Browser evidence still required

A new real reviewed measurement cannot be entered honestly without a qualified calibration record, suitable reference segment and reviewed lumen boundaries. No such real-image reference is currently available. Therefore no patient-like browser record was fabricated merely to produce a screenshot.

When eligible evidence exists, the browser check must record one candidate, save the reviewed MLD/RVD evidence, refresh, verify the same record, reopen its report/ZIP, compare IDs and values with the API, exercise invalid inputs, and verify an unauthorized role cannot create or export the measurement.


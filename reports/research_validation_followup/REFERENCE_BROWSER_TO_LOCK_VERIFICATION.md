# Browser-to-lock status

## Resolved and verified - 11 November 2026

After the owner enabled extension file-URL permission, the actual Chrome file chooser loaded the labelled synthetic image successfully. MLD endpoints (100,100)-(100,120) and RVD endpoints (100,200)-(100,240) were entered through the page controls. The page calculated 20 and 40 source pixels. All required identities and provenance were entered as synthetic software evidence, the draft was saved, the page refreshed, and the original image reselected. The draft restored the exact values, endpoints, quality and provenance.

Chrome downloaded the real CSV, JSON and snapshot receipt to Downloads. The backend imported that exact CSV using `app.reference_collection`, verified original-image hash and endpoint widths, and locked one synthetic row at `/tmp/corovision-reference-browser-lock-20261111-v1`. Reopening returned MLD 20 and RVD 40. The CSV SHA-256 matched the browser receipt: `51ad52e7426d85e0e9f4232ca4450e0eaf0cfdceed44f32edec63c0377bb1543`. Screenshot: `REFERENCE_ROUNDTRIP_BROWSER.jpg`.

The software round trip is verified. This synthetic lock is separate from the real ARCADE pilot, whose completed reference count remains zero. Zoom/pointer placement at multiple magnifications was not exercised in this check; endpoint entry used original-coordinate numeric controls. Tampering rejection remains covered by the existing backend integration test.

## Historical blocker

The actual Chrome reference page was opened with the isolated synthetic fixture prepared at `/tmp/corovision-reference-browser-synthetic/synthetic-reference.png`. Browser file selection failed before image loading because the ChatGPT extension requires Allow access to file URLs. The native UI fallback could observe Chrome but failed input with noWindowsAvailable. Permission was not expanded automatically.

Consequently actual endpoint entry, zoom/pan coordinate testing, downloaded CSV import and browser-generated lock equality remain blocked in this browser configuration. Backend synthetic endpoint/CSV/image-hash/lock/reopen/tamper tests pass. They are not represented as the missing browser test.

To resume: enable local file URL access for the Chrome ChatGPT extension, reload `reference-measurement.html`, use the labelled synthetic image, enter 20px and 40px endpoints, export CSV, run `python -m app.reference_collection` against that exact downloaded file, and verify the receipt. Keep all synthetic rows outside the ARCADE pilot.

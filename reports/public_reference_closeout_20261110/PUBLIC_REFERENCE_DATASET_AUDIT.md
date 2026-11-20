# Public reference dataset audit

| Release | Verified intake | Eligible use and open checks |
|---|---|---|
| [ARCADE](https://zenodo.org/records/10390295) | Zenodo metadata lists CC0 for this record and arcade.zip MD5 c5b1973ade06f7dff210f878161e1a76. PNG and COCO polygon tasks are separate. | Segmentation and lesion localization. Resolve the 996 same-split filename/hash permutation against original annotations, bind exact remote version, and verify checkpoint exposure. |
| [CADICA v5](https://data.mendeley.com/datasets/p9bpx9ctcv/5) | CC BY 4.0, 42 patients, selected-frame boxes, patient/video/frame identifiers and video-level lesion status. The local 188051456-byte ZIP failed `zipfile.is_zipfile`. Published archive is 3076112179 bytes. | Selected-frame localization after intact archive intake. Video labels alone cannot establish every frame as a reviewed negative. |
| [AngioCAD](https://zenodo.org/records/15826856) | CC BY 4.0. Both XLSX files downloaded and matched publisher MD5 using `md5 AngioCAD_*.xlsx`. Labels fc97ffc2978f6cee93a1059e8b1c282f. Features 1617d242df42367787f445392729f35e. Read headers with `openpyxl.load_workbook(..., read_only=True)`. | ID, series and segment labels, plus Gensini score in Features. Headers do not establish same-frame lesion geometry, calibration, or QCA lumen measurements. Image archives were outside this metadata intake. |
| [ImageCAS-X v2](https://zenodo.org/records/23562647) | CC BY 4.0. Release lists corrected lumen and centerline artifacts. ZIP MD5 d8fb4a91cd2d494af8db9153bf774e12. | Candidate for separate 3D CTA evaluation. Verify release, spatial orientation, pairing and checkpoint overlap with ImageCAS before evaluating. |
| CARDIAG | Existing intake recorded 645 samples and 122 groups. Author correspondence reports absence of QCA/lumen measurements. | Group-aware evaluation candidate after data pairing, eligibility and exposure checks. See [intake](../cardiag_intake_20261110/REVIEW.md). |

Metadata inspection used the publishers' release pages and Zenodo API records. CADICA intake receipts are under `/Volumes/One Touch/execution_readiness_20261030/reference_validation_20261105/`. No new benchmark was scored.

### Official archive index follow-up

HTTP range requests returned 206 for the official ARCADE and CADICA ZIP central directories. Python `zipfile` read their member indexes. The two ARCADE validation COCO members were retrieved by byte range, decompressed and checked against their CRCs and previously recorded SHA-256 hashes. All 400 validation image-ID, filename and annotation-ID joins matched. Each ARCADE task has 1000 train, 200 validation and 300 test PNG entries. The source has 132 repeated PNG size/CRC groups, with one spanning split names. This is a duplicate screen. Rasterized mask alignment, near duplicates and patient independence remain unverified.

CADICA's publisher index lists 31,500 PNGs, 382 selected-frame lists and 42 each of lesion and nonlesion video lists. `cmp -n 65536` showed that the local file is a different byte stream. `tar -tf` found a nested CADICA.zip entry and failed with a decompression error. The local wrapper cannot be resumed as the official archive. Index membership does not certify frame-level negative scope or the completeness of local data.

Exact byte ranges, digests and counts are in the [official archive receipt](OFFICIAL_ARCHIVE_INDEX_RECEIPT.json).

The publisher README member also passed its ZIP CRC check. Its SHA-256 matches the recovered One Touch sidecar. It defines expert-selected keyframes, manually labelled boxes and video-level visible-lesion status. This verifies the README provenance and documented annotation scope. Full member bytes and frame-to-box joins still need verification.

Full `curl -fLsS` transfers timed out with exit 28. CADICA received 34,484,667 of 3,076,112,179 bytes in 100 seconds. ARCADE received 45,887,024 of 451,573,813 bytes in 180 seconds. The official partial files are under `/tmp/corovision-official-intake/` and are separate from the damaged local wrapper. Resume the official transfers and verify the publisher digests before using full-archive contents. The [receipt generator](audit_official_archive_indexes.py) uses the byte ranges in the receipt and reads no images.

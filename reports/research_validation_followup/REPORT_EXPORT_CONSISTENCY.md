# Report/export consistency verification

On 11 November 2026, Chrome saved report v3 `f8777b6a-0b2f-407c-ba1f-3d66dd5167aa` for Case 60 and downloaded `DEMO-DCA1-003-20261109-research-v3.zip` (235,813 bytes).

ZIP SHA-256: `407358697b7a3b5283e25891d94aeb6886b91015c6358b62af64427505e783c4`.

Every manifest artifact length and hash matched. The archive contained report JSON, CSV, PDF and manifest. Automatic measurement arrays in JSON and CSV were exactly equal and contained assessment `124d94439d965864fe4898ceab59798eaa842fd02ae3bd461100f10179ae4994` with C1/C2/C3 abstentions for low local boundary contrast. PDF export completed and its bytes were bound by the same manifest; visual PDF layout QA and textual field equality are not asserted by the hash check.

New report snapshots preserve automatic measurement records. PDF now includes assessment identity, candidate/status, source-pixel widths, narrowing, sensitivity range, grade/indeterminate and reasons. CSV includes full structured evidence and JSON retains coordinates, provenance and hashes. Existing reports remain immutable; new measurements do not retroactively edit historical report snapshots.

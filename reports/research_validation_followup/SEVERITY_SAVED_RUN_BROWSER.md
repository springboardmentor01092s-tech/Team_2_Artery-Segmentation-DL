# Saved-run browser verification - 11 November 2026

Chrome opened the actual signed-in local application. Image Review restored Case 60 (`DEMO-DCA1-003-20261109`), image `dca1-003.png` and run `d0286ecd-e383-4f16-8ecb-9e662c8df223`. Clicking the assessment button invoked the saved-artifact geometry pipeline. Candidates C1, C2 and C3 retained their identities, associated geometrically with path P1, and abstained for low local boundary contrast. No narrowing or severity value was invented.

Browser refresh restored assessment `124d94439d965864fe4898ceab59798eaa842fd02ae3bd461100f10179ae4994`. The UI retained all three candidate abstentions. A new report v3 was saved through the UI and its Evidence ZIP downloaded through the UI. The ZIP contains report JSON/CSV/PDF and manifest. Every manifest SHA-256 and byte length matched. The CSV structured automatic-measurement records exactly matched the JSON records. The receipt is `SAVED_RUN_BROWSER_RECEIPT.json`.

Screenshots: `SAVED_RUN_MEASUREMENT_BROWSER.jpg` and `MEASUREMENT_REPORT_BROWSER.jpg`.

The manual synthetic CSV browser test could not load its image: the Chrome extension refused fileChooser.setFiles because file-URL access is disabled. The native fallback reported no usable window for input. No browser permission was changed. The synthetic backend round trip remains verified, but the actual manual browser download-to-lock workflow and new-image browser upload remain unverified this pass.

The saved-case result establishes persistence and appropriate abstention on this case, not patient-image measurement accuracy. No fresh model inference or training was dispatched.

# Calibration and units audit

| Evidence source | Rows | Unit permitted | Physical calibration |
|---|---:|---|---|
| ARCADE pilot package | 20 candidate lesions | `source_px` | None verified |
| Independently measured rows | 0 | Unavailable | 0 verified |
| Nine synthetic phantoms | 9 fixtures / 26 eligible sites | synthetic pixels | Known digital geometry only |
| Case 60 | 3 candidates | saved source-pixel mask profiles | No MLD/RVD calibration |

The ARCADE PNG/COCO files do not provide trustworthy image-plane millimetre calibration. X-ray magnification and vessel-plane geometry prevent an assumed pixel-to-millimetre conversion. The pilot worksheet therefore defaults to `source_px`. A future `mm` row must include a calibration identifier and evidence that the scale applies to the vessel plane.

Pixel-based MLD/RVD can support relative narrowing agreement under consistent same-image geometry. It cannot establish physical millimetre accuracy or expert QCA agreement.


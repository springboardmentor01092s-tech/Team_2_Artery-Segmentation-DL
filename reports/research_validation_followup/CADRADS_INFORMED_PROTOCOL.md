# CAD-RADS-informed XCA Research Severity v1.0.0

Protocol ID: `COROVISION_CADRADS_INFORMED_XCA`. State: inactive until an actual researcher authorization event. Scientific status: experimental/unvalidated. Applicable workflow: per-lesion 2D invasive coronary X-ray angiography, with source-pixel diameter ratios and required quality/sensitivity evidence.

Source: Cury et al., CAD-RADS 2.0, JACC Cardiovascular Imaging (2022), DOI `10.1016/j.jcmg.2022.07.002`; synchronous consensus publication DOI `10.1148/ryct.220183`.

The published system applies to CCTA and patient-level reporting. CoroVision does not implement its management recommendations, plaque burden, patient aggregation or official CAD-RADS diagnosis.

| Unrounded narrowing | New XCA research output | Original experiment |
|---|---|---|
| Exactly 0% | No measured narrowing | Normal |
| (0,25%) | Minimal | Mild |
| [25,50%) | Mild | Mild |
| [50,70%) | Moderate | Moderate |
| [70,90%) | Severe | Severe |
| [90,100%) | Severe | Critical |
| Exactly 100% | Possible occlusion; assessment required | Same separate status |

The continuous interval (0,25%) extends the published integer presentation of 1–24%. Values below 1% qualify only when their recorded uncertainty does not include zero. Category assignment uses full precision; display rounding never changes a category. Missing measurements, authorization, exact protocol version or uncertainty withholds grading. Sensitivity crossing zero, 25, 50, 70 or 100 also withholds grading.

## Use in the application

Open Image Review -> Severity Assessment -> Research protocol. The new protocol is the recommended option in the review selector. The original five-category experiment remains selectable and historical assessments are preserved. Merely selecting an option does not authorize it. A researcher/admin account can check the explicit Research Mode authorization statement and press Record researcher authorization. Actor, timestamp, version, bands, applicability and research restriction are saved in the authorization history.

Then assess the saved run. Eligible measurement records use the active applicable protocol and store its identity and uncertainty result. Existing assessments/reports are not recomputed by changing protocol selection. Candidate abstention remains possible; Case 60 currently abstains for low local boundary contrast and must not be assigned a category.

The manual 20-image ARCADE reference pilot remains exploratory because of checkpoint exposure. No genuine reference pairs or clinical accuracy results were created by this protocol change.

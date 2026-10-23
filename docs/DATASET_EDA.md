# ARCADE exploratory data analysis

Source: https://zenodo.org/records/10390295

## Inventory

| Task | Split | Images | Annotations | Observed categories |
|---|---|---:|---:|---:|
| Artery regions (`syntax`) | Train | 1,000 | 4,976 | 25 |
| Artery regions (`syntax`) | Validation | 200 | 1,168 | 25 |
| Artery regions (`syntax`) | Test | 300 | 1,672 | 24 |
| Stenosis | Train | 1,000 | 1,625 | 1 |
| Stenosis | Validation | 200 | 406 | 1 |
| Stenosis | Test | 300 | 386 | 1 |

All listed images are 512×512 PNGs. All annotation image references resolve,
and every annotation has polygon coordinates and a bounding box. No files are
missing from the six splits.

The complete dataset contains **3,000 images and 10,233 polygon annotations**.

## Annotation density and negative images

| Task | Split | Annotated / total | Mean annotations/image | Median | Range |
|---|---|---:|---:|---:|---:|
| Syntax | Train | 1,000 / 1,000 | 4.976 | 5 | 2–9 |
| Syntax | Validation | 200 / 200 | 5.840 | 6 | 3–11 |
| Syntax | Test | 300 / 300 | 5.573 | 5 | 2–9 |
| Stenosis | Train | 997 / 1,000 | 1.625 | 1 | 0–7 |
| Stenosis | Validation | 200 / 200 | 2.030 | 2 | 1–8 |
| Stenosis | Test | 300 / 300 | 1.287 | 1 | 1–4 |

The three unannotated stenosis training images are retained as legitimate
negative samples. They must not be silently dropped. Stenosis annotation density
also differs between validation and test, so metrics should be reported per
official split rather than inferred from a pooled dataset.

## Geometry and intensity findings

- Syntax median polygon areas are 1,488 px² (train), 1,370 px² (validation),
  and 1,346.5 px² (test).
- Stenosis median polygon areas are 983 px² (train), 800.5 px² (validation),
  and 1,581.5 px² (test). The larger test lesions indicate a geometry shift that
  should be considered when interpreting test performance.
- Mean grayscale intensity differs by split. Syntax train averages 113.22,
  validation 134.57, and test 124.02; stenosis train averages 121.86,
  validation 134.20, and test 118.39. This supports per-image conservative
  normalization and explicit preprocessing ablations.
- Source modes are mixed: syntax train has 451 grayscale and 549 RGB PNGs;
  stenosis train has 699 grayscale and 301 RGB PNGs. Validation and test files
  are grayscale. All are converted consistently to one grayscale channel.

## Class imbalance

All 25 syntax categories appear in train and validation, while category 12
(`10a`) is absent from test. In syntax train, category 6 (`6`) has 537
annotations and category 5 (`5`) has 525, whereas category 12 (`10a`) has only
one annotation. Multiclass experiments therefore require class-aware metrics
and should not rely on aggregate pixel accuracy alone.

## Annotation interpretation

- The `syntax` category dictionary has 26 entries, but its annotations use
  IDs 1–25. Category 26 is named `stenosis` and appears in the stenosis task.
- The stenosis task uses category 26 for all annotated lesions.
- Polygons are lists of alternating x/y coordinates; boxes are x/y/width/height.
- The overlaid examples in `docs/eda/` visually align with vessels and lesions.

## Split and modeling cautions

- Train, validation, and test folders reuse filenames such as `1.png`; they
  are different images. Always include task and split in a file identifier.
- Within `syntax`, no byte-identical images were found across splits. In
  `stenosis`, image ID 218 in train and image ID 155 in validation are
  byte-identical. The preprocessing pipeline reports this as a leakage warning
  and does not silently alter the official split.
- Across tasks, train and validation images do not match byte-for-byte.
  The two test sets share 123 byte-identical images.
- Artery categories are strongly imbalanced: some train classes have hundreds
  of annotations, while category ID 12 has only one. Start with binary vessel
  segmentation, then evaluate multiclass segmentation separately.
- Image-level duplicates were checked by SHA-256. This does not rule out
  different frames from the same patient or video across splits because the
  release lacks a verified patient identifier in this audit.

## Preview images

- `eda/syntax_train_example.png`: nine artery-region polygons over one frame.
- `eda/stenosis_train_example.png`: three stenosis polygons over one frame.

Recreate the preview images with `python3 scripts/make_eda_previews.py`.

## Reproducible EDA artifacts

Run the complete analysis with:

```bash
python3 scripts/run_dataset_eda.py --data-root arcade --output-root outputs/eda
```

The command analyzes all 3,000 images and writes:

- `eda_summary.json`: split-level image, annotation, geometry, intensity, mode,
  and limitation summaries.
- `class_distribution.csv`: every used category count by task and split.
- `exact_duplicates.csv`: named within-task cross-split and cross-task exact
  duplicate groups.
- `split_distribution.png`, `syntax_train_class_distribution.png`, and
  `intensity_histogram.png`: reviewable visual summaries.

Automated EDA and preprocessing tests are in `tests/preprocessing/`.

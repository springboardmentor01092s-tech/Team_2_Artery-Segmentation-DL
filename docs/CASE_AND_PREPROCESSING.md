# De-identified case management and preprocessing

## Cases

Each case has a generated UUID case ID and a user-facing case code. The optional
patient ID is a **pseudonym**, not a real medical record number. Age is stored as
a band, not an exact age. Gender, medical history, and risk factors use bounded
choices; clinical notes are limited to 500 characters. Obvious email addresses
and phone numbers are rejected, but this is not a complete de-identification
system. Do not enter names, birth dates, addresses, or other identifiers.

Cases also store imaging modality (XCA or CTA), coronary anatomical region,
optional de-identified scan date, upload status, and images. The active trained
model supports XCA only; CTA may be stored for preparation but is refused for
AI analysis. The image record stores source dimensions, captured DICOM pixel
spacing when available, calculated spacing for the resized content, optional
ROI, selected DICOM frame or scanned-PDF page, and performed preprocessing steps.

The API supports create, list, view, and metadata update. A case owner or
administrator may access it. Every analysis creates a new `analysis_events`
record and a distinct overlay file, while `analysis_runs` retains the latest
result for older clients. History can be viewed per image or case. Two runs on
the same image can be compared by model version and predicted mask pixel counts.
These differences are **not** clinical progression measurements.

## Upload and model-input pipeline

1. Validate extension, file size (50 MB maximum), decoder, dimensions, and image format.
   DICOM uploads with common identifying patient tags are rejected. Only
   public/de-identified source files are appropriate.
2. For multi-frame grayscale DICOM, select an explicit zero-based frame. A
   single-frame DICOM does not need selection. For a scanned PDF, select one
   zero-based page; page zero is used by default. PDF rasterization requires
   Poppler's `pdftoppm` on the server.
3. Convert supported PNG, JPEG, WebP, TIFF, BMP, GIF, AVIF, JPEG 2000, PNM,
   PCX, TGA, ICO, selected DICOM frame, or scanned-PDF page to grayscale.
   Decoder support for optional raster formats depends on the Pillow build.
   DICOM pixel values
   are robustly scaled between the first and 99th percentiles and MONOCHROME1
   is inverted. DICOM `PixelSpacing` or `ImagerPixelSpacing` is retained as
   source metadata when present.
4. Standard preprocessing preserves 8-bit source intensity and vessel detail.
   DICOM and high-bit-depth raster data receive documented percentile scaling.
   A researcher can select the Research profile and independently opt in to a
   3×3 median filter or clipped autocontrast; these are off by default. The
   original upload remains stored for comparison. Optionally crop an explicit
   ROI in **source-image** `x,y,width,height` pixels. The ROI must lie within
   the image and be at least 32×32 pixels.
5. Resize while preserving aspect ratio and pad to a 512×512 uint8 PNG
   preview. The original source is stored separately in local ignored storage.
   Source spacing remains unchanged in metadata; processed spacing describes
   the unpadded resized content. Padding is not a physical image region.
6. At AI analysis, downsample the preview to 128×128, apply the trained
   model's 3×3 median filter and clipped autocontrast, and scale intensities to
   [0,1]. These model-input transforms match the ARCADE training pipeline and
   are recorded separately from optional upload-time research enhancement.
   The model outputs binary pixel masks and a colored overlay.

ARCADE contains independent 2D PNG frames and COCO polygons; it has no ordered
3D series or physical pixel spacing. Therefore 3D volume construction and
registration are not run on ARCADE. The preprocessing library can stack
explicitly ordered slices only when valid voxel spacing is supplied. Training
augmentation is applied only to training image/mask pairs and is not part of
upload. Uploaded source hashes are retained for exact duplicate checks within
a case. The processing record includes pipeline version, profile, options,
dimensions, spacing warning, selected frame/page/ROI, source and preview
hashes, applied steps, and timestamp. Original DICOM spacing does not
automatically calibrate a stenosis percentage.

Office documents (DOCX, spreadsheets, slides, text), SVG, and unknown formats
are rejected because they do not provide a trustworthy medical image frame for
the 2D model. A PDF upload is a page rasterization, not document analysis or
patient de-identification. Multi-file upload adds each accepted image as a
separate case image. 3D reconstruction and registration are outside the current
XCA model path; an ordered volume cannot be inferred from arbitrary files.

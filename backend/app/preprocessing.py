from io import BytesIO
import math
import shutil
import subprocess

import numpy as np
from PIL import Image as PILImage, ImageFilter, ImageOps, UnidentifiedImageError

TARGET_SIZE = 512
STANDARD_PIPELINES = {
    "baseline": (False, False),
    "denoise": (True, False),
    "contrast": (False, True),
    "balanced": (True, True),
}
RASTER_FORMATS = {
    "PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp",
    "TIFF": "image/tiff", "BMP": "image/bmp", "GIF": "image/gif",
    "AVIF": "image/avif", "JPEG2000": "image/jp2", "PPM": "image/x-portable-anymap",
    "PCX": "image/x-pcx", "TGA": "image/x-tga", "ICO": "image/x-icon",
}
SUPPORTED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".gif",
    ".avif", ".jp2", ".j2k", ".ppm", ".pgm", ".pnm", ".pcx", ".tga", ".ico",
    ".dcm", ".dicom", ".pdf",
}
class InvalidImage(ValueError):
    pass


def content_geometry(width, height, roi_box=None):
    """Record resize/padding geometry using the same aspect rule as Pillow."""
    crop_width = roi_box[2]-roi_box[0] if roi_box else width
    crop_height = roi_box[3]-roi_box[1] if roi_box else height
    out_width, out_height = crop_width, crop_height
    if max(crop_width, crop_height) > TARGET_SIZE:
        aspect = crop_width/crop_height
        if aspect <= 1:
            out_height = TARGET_SIZE
            value = TARGET_SIZE*aspect
            out_width = max(1, min(math.floor(value), math.ceil(value), key=lambda n: abs(aspect-n/TARGET_SIZE)))
        else:
            out_width = TARGET_SIZE
            value = TARGET_SIZE/aspect
            out_height = max(1, min(math.floor(value), math.ceil(value), key=lambda n: abs(aspect-TARGET_SIZE/n) if n else float("inf")))
    return {"content_size_xy": [out_width, out_height],
            "padding_left_top_xy": [(TARGET_SIZE-out_width)//2, (TARGET_SIZE-out_height)//2],
            "source_roi_origin_xy": list(roi_box[:2]) if roi_box else [0, 0],
            "source_pixels_per_content_pixel_xy": [crop_width/out_width, crop_height/out_height]}


def prepare_image(raw: bytes, filename: str, roi_box: tuple[int, int, int, int] | None = None,
                  frame_index: int | None = None, page_index: int | None = None,
                  denoise: bool = False, enhance: bool = False,
                  processing_steps: list[str] | None = None) -> tuple[bytes, int, int, str, str | None]:
    """Return a 512px padded grayscale PNG, original dimensions, media type, spacing."""
    spacing = None
    if filename.lower().endswith((".dcm", ".dicom")):
        if page_index is not None:
            raise InvalidImage("PDF page selection is only available for PDF files")
        try:
            import pydicom

            ds = pydicom.dcmread(BytesIO(raw), force=False)
            identifying_tags = ("PatientName", "PatientID", "PatientBirthDate", "PatientAddress",
                                "PatientTelephoneNumbers", "ReferringPhysicianName")
            if any(str(getattr(ds, tag, "")).strip() for tag in identifying_tags):
                raise InvalidImage("Remove identifying DICOM tags before upload")
            rows, columns = int(getattr(ds, "Rows", 0)), int(getattr(ds, "Columns", 0))
            if rows < 32 or columns < 32 or rows > 8192 or columns > 8192:
                raise InvalidImage("DICOM dimensions must be between 32 and 8192 pixels")
            frame_count = int(getattr(ds, "NumberOfFrames", 1))
            if frame_count > 1 and frame_index is None:
                raise InvalidImage("Choose a frame index for a multi-frame DICOM study")
            if frame_count > 1 and (frame_index < 0 or frame_index >= frame_count):
                raise InvalidImage("DICOM frame index is outside the study")
            if frame_count == 1 and frame_index not in (None, 0):
                raise InvalidImage("Single-frame DICOM has only frame 0")
            from pydicom.pixels import pixel_array
            pixels = pixel_array(BytesIO(raw), index=frame_index if frame_count > 1 else None)
            if pixels.ndim != 2:
                raise InvalidImage("Only single-frame 2D DICOM images are supported")
            from pydicom.pixels import apply_modality_lut
            pixels = np.asarray(apply_modality_lut(pixels, ds), dtype=np.float32)
            if not np.isfinite(pixels).all():
                raise InvalidImage("DICOM contains non-finite intensities")
            if processing_steps is not None:
                processing_steps.append("dicom_modality_lut_or_rescale")
            low, high = np.percentile(pixels, [1, 99])
            pixels = np.clip((pixels - low) / max(high - low, 1e-6), 0, 1)
            if processing_steps is not None:
                processing_steps.append("dicom_percentile_intensity_normalization")
            if getattr(ds, "PhotometricInterpretation", "") == "MONOCHROME1":
                pixels = 1 - pixels
            img = PILImage.fromarray((pixels * 255).astype("uint8")).convert("L")
            if processing_steps is not None:
                processing_steps.append("grayscale_conversion")
            raw_spacing = getattr(ds, "PixelSpacing", None) or getattr(ds, "ImagerPixelSpacing", None)
            if raw_spacing:
                if len(raw_spacing) != 2 or not np.isfinite([float(x) for x in raw_spacing]).all() or min(float(x) for x in raw_spacing) <= 0:
                    raise InvalidImage("DICOM pixel spacing must contain two positive finite values")
                spacing = ",".join(str(x) for x in raw_spacing)
            media_type = "application/dicom"
        except ImportError:
            raise InvalidImage("DICOM support requires pydicom")
        except InvalidImage:
            raise
        except Exception as exc:
            raise InvalidImage(f"Unreadable DICOM: {type(exc).__name__}") from exc
    elif filename.lower().endswith(".pdf"):
        if frame_index is not None:
            raise InvalidImage("DICOM frame selection is only available for DICOM files")
        if not raw.startswith(b"%PDF-"):
            raise InvalidImage("File is not a valid PDF")
        page = 0 if page_index is None else page_index
        if page < 0 or page > 999:
            raise InvalidImage("PDF page index must be between 0 and 999")
        converter = shutil.which("pdftoppm")
        if not converter:
            raise InvalidImage("PDF conversion requires Poppler's pdftoppm on the server")
        try:
            result = subprocess.run(
                [converter, "-f", str(page + 1), "-l", str(page + 1),
                 "-singlefile", "-scale-to", "2048", "-png", "-"],
                input=raw, capture_output=True, timeout=20, check=False,
            )
            if result.returncode or not result.stdout:
                raise InvalidImage("PDF page could not be rendered; check the page index and file")
            img = PILImage.open(BytesIO(result.stdout))
            img.load()
            media_type = "application/pdf"
            img = img.convert("L")
            if processing_steps is not None:
                processing_steps.extend(["pdf_page_rasterization", "grayscale_conversion"])
        except subprocess.TimeoutExpired as exc:
            raise InvalidImage("PDF conversion timed out") from exc
        except (UnidentifiedImageError, OSError, PILImage.DecompressionBombError) as exc:
            raise InvalidImage("PDF page is unreadable") from exc
    else:
        if frame_index is not None:
            raise InvalidImage("Frame selection is only available for DICOM")
        if page_index is not None:
            raise InvalidImage("PDF page selection is only available for PDF files")
        try:
            img = PILImage.open(BytesIO(raw))
            if img.format not in RASTER_FORMATS:
                raise InvalidImage("Unsupported image encoding")
            if img.width < 32 or img.height < 32 or img.width > 8192 or img.height > 8192:
                raise InvalidImage("Image dimensions must be between 32 and 8192 pixels")
            img.load()
            media_type = RASTER_FORMATS[img.format]
            img = ImageOps.exif_transpose(img)
            if img.mode in {"I", "I;16", "I;16B", "I;16L", "F"}:
                values = np.asarray(img, dtype=np.float32)
                finite = values[np.isfinite(values)]
                if finite.size != values.size:
                    raise InvalidImage("Image contains non-finite pixel values")
                low, high = np.percentile(finite, [1, 99])
                gray = np.clip((values - low) / max(float(high - low), 1e-6), 0, 1)
                img = PILImage.fromarray((gray * 255).astype("uint8"))
                if processing_steps is not None:
                    processing_steps.append("robust_high_bit_depth_intensity_normalization")
            else:
                img = img.convert("L")
            if processing_steps is not None:
                processing_steps.append("grayscale_conversion")
        except (UnidentifiedImageError, OSError, PILImage.DecompressionBombError) as exc:
            raise InvalidImage("Unreadable image") from exc
    width, height = img.size
    if width < 32 or height < 32 or width > 8192 or height > 8192:
        raise InvalidImage("Image dimensions must be between 32 and 8192 pixels")
    # Enhancement is opt-in: smoothing/equalization can erase narrow vessel edges.
    if denoise:
        img = img.filter(ImageFilter.MedianFilter(size=3))
        if processing_steps is not None:
            processing_steps.append("optional_median_noise_reduction")
    if enhance:
        img = ImageOps.autocontrast(img, cutoff=1)
        if processing_steps is not None:
            processing_steps.append("optional_clipped_autocontrast")
    if roi_box is not None:
        left, top, right, bottom = roi_box
        if left < 0 or top < 0 or right > width or bottom > height or right - left < 32 or bottom - top < 32:
            raise InvalidImage("ROI must be inside the image and at least 32×32 pixels")
        img = img.crop(roi_box)
        if processing_steps is not None:
            processing_steps.append("roi_crop")
    img.thumbnail((TARGET_SIZE, TARGET_SIZE), PILImage.Resampling.LANCZOS)
    if processing_steps is not None:
        processing_steps.extend(["aspect_preserving_resize", "512x512_padding", "save_lossless_png_preview"])
    canvas = PILImage.new("L", (TARGET_SIZE, TARGET_SIZE), 0)
    canvas.paste(img, ((TARGET_SIZE - img.width) // 2, (TARGET_SIZE - img.height) // 2))
    out = BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue(), width, height, media_type, spacing


def processed_spacing_mm(spacing: str | None, width: int, height: int,
                         roi_box: tuple[int, int, int, int] | None) -> str | None:
    """Preserve physical spacing for the unpadded, resized 2D content."""
    if not spacing:
        return None
    try:
        row_mm, col_mm = (float(value) for value in spacing.split(","))
        crop_width = roi_box[2] - roi_box[0] if roi_box else width
        crop_height = roi_box[3] - roi_box[1] if roi_box else height
        if not np.isfinite([row_mm, col_mm]).all() or min(row_mm, col_mm) <= 0:
            return None
        resized_width, resized_height = content_geometry(width, height, roi_box)["content_size_xy"]
        return f"{row_mm * crop_height / resized_height:.8g},{col_mm * crop_width / resized_width:.8g}"
    except (TypeError, ValueError, ZeroDivisionError):
        return None

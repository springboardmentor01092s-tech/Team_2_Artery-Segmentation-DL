export const standardPipelines = [
  { id: "baseline", title: "Baseline", description: "Validate → grayscale / high-bit-depth normalization → optional ROI → aspect-preserving resize and padding. Matches the existing default.", path: "Validate → Grayscale / intensity normalization → Optional ROI → Resize and padding → Quality check" },
  { id: "denoise", title: "Noise Reduction", description: "Standard preparation with a 3×3 median filter before ROI and resizing. For comparing images with isolated pixel noise.", path: "Validate → Grayscale / intensity normalization → Median noise reduction → Optional ROI → Resize and padding → Quality check" },
  { id: "contrast", title: "Contrast Enhancement", description: "Standard preparation with 1% clipped autocontrast before ROI and resizing. For comparing low-contrast inputs.", path: "Validate → Grayscale / intensity normalization → Clipped autocontrast → Optional ROI → Resize and padding → Quality check" },
  { id: "balanced", title: "Noise + Contrast", description: "Median noise reduction followed by clipped autocontrast, then optional ROI, resize and padding.", path: "Validate → Grayscale / intensity normalization → Median noise reduction → Clipped autocontrast → Optional ROI → Resize and padding → Quality check" },
] as const;
export type StandardPipeline = typeof standardPipelines[number]["id"];

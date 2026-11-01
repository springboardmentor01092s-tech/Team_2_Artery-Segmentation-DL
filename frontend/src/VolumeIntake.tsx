import { useState } from "react";
import { apiUrl } from "./api";
import { Button } from "./components/prismui/button";
import VolumeInference from './VolumeInference';

export default function VolumeIntake({ caseId, token, inferenceEligible = false, readOnly = false,anatomy='coronary' }: { caseId: string; token: string; inferenceEligible?: boolean; readOnly?: boolean;anatomy?:string }) {
  const [source, setSource] = useState<File | null>(null);
  const [mask, setMask] = useState<File | null>(null);
  const [reference, setReference] = useState<File | null>(null);
  const [spacing, setSpacing] = useState("");
  const [roi, setRoi] = useState("");
  const [slice, setSlice] = useState("");
  const [denoise, setDenoise] = useState(false);
  const [enhance, setEnhance] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function prepare(event: React.FormEvent) {
    event.preventDefault();
    if (!source || busy) return;
    setBusy(true); setMessage(""); setError("");
    try {
      for (const file of [source, mask, reference]) {
        if (file && (!/\.nii(\.gz)?$/i.test(file.name) || !file.size || file.size > 50*1024*1024))
          throw new Error("Use NIfTI files up to 50 MB each. Larger volumes and DICOM series require offline preparation.");
      }
      const body = new FormData();
      body.append("file", source);
      if (mask) body.append("mask", mask);
      if (reference) body.append("reference", reference);
      if (spacing) body.append("spacing", spacing);
      if (roi) body.append("roi", roi);
      if (slice) body.append("slice_index", slice);
      body.append("denoise", String(denoise)); body.append("enhance", String(enhance));
      const response = await fetch(apiUrl(`/api/cases/${caseId}/volumes/prepare`), {
        method: "POST", headers: { Authorization: `Bearer ${token}` }, body,
      });
      if (!response.ok) throw new Error((await response.json()).detail || "Preparation failed");
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url; link.download = "corovision_volume_prepared.zip"; link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
      setMessage("Preparation complete. Download includes preserved originals, prepared NIfTI, model-input arrays, selected-slice preview and geometry record. Inspect them before model use.");
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }

  return <section className="intake-pipeline">
    {inferenceEligible && <VolumeInference caseId={caseId} token={token} readOnly={readOnly} anatomy={anatomy} />}
    {!readOnly && <details><summary>Optional generic volume preparation and export (not model inference)</summary>
    <h3>3D volume preparation · Research only</h3>
    <p>Separate from 2D X-ray inference. NIfTI files must be de-identified, in millimetres, and contain at most 32 million voxels. No 3D prediction or training starts here.</p>
    <form className="case-details-form" onSubmit={prepare}>
      <label>Source volume (.nii / .nii.gz)<input type="file" accept=".nii,.nii.gz" required onChange={e => setSource(e.target.files?.[0] || null)} /></label>
      <label>Optional categorical mask (same source geometry)<input type="file" accept=".nii,.nii.gz" onChange={e => setMask(e.target.files?.[0] || null)} /></label>
      <label>Optional fixed reference — enables rigid registration<input type="file" accept=".nii,.nii.gz" onChange={e => setReference(e.target.files?.[0] || null)} /></label>
      {reference && <p className="message warning">Registration is an estimate, not proof of anatomical alignment. Visually review the exported transform and resampled volume. ROI coordinates apply to the reference grid.</p>}
      <label>Target spacing x,y,z (mm; blank preserves spacing)<input value={spacing} onChange={e => setSpacing(e.target.value)} placeholder="e.g. 1,1,1" /></label>
      <label>Optional ROI x,y,z,width,height,depth (voxels)<input value={roi} onChange={e => setRoi(e.target.value)} placeholder="e.g. 0,0,0,64,64,32" /></label>
      <label>Axial slice index (zero-based; blank selects middle)<input type="number" min="0" step="1" value={slice} onChange={e => setSlice(e.target.value)} /></label>
      <div className="preprocessing-options">
        <label><input type="checkbox" checked={denoise} onChange={e => setDenoise(e.target.checked)} />Optional 3D median denoising</label>
        <label><input type="checkbox" checked={enhance} onChange={e => setEnhance(e.target.checked)} />Optional local contrast enhancement</label>
        <small>Enhancement can alter fine vessels. Training-only augmentation is not applied to uploaded evaluation cases.</small>
      </div>
      <Button type="submit" disabled={!source || busy}>{busy ? "Preparing volume…" : "Prepare and download volume"}</Button>
      {error && <p className="message error" role="alert">{error}</p>}
      {message && <p className="message success" role="status">{message}</p>}
    </form></details>}
  </section>;
}

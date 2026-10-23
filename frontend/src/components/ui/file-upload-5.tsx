import { useEffect, useRef, useState } from "react";
import { FileImage, UploadCloud, X } from "lucide-react";
import { Card } from "@/components/ui/card";

const formats = ["png", "jpg", "jpeg", "webp", "tif", "tiff", "bmp", "gif", "avif", "jp2", "j2k", "ppm", "pgm", "pnm", "pcx", "tga", "ico", "dcm", "dicom", "pdf"];
const maxFileSizeMb = 50;

interface DocumentUploaderProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
}

function ImageRow({ file, onRemove }: { file: File; onRemove: () => void }) {
  const [preview, setPreview] = useState("");
  useEffect(() => {
    if (!/\.(png|jpe?g|webp|gif|bmp)$/i.test(file.name)) return;
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  return <div className="medical-file-row">
    {preview ? <img src={preview} alt="Selected image preview" /> : <FileImage aria-hidden="true" size={30} />}
    <div><strong title={file.name}>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(2)} MB · Ready to validate</small></div>
    <button type="button" aria-label={`Remove ${file.name}`} title="Remove file" onClick={onRemove}><X aria-hidden="true" size={18} /></button>
  </div>;
}

/** Watermelon file-upload-5 adapted for medical image batches. */
export default function DocumentUploader({ files, onFilesChange }: DocumentUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");

  function add(incoming: File[]) {
    const accepted: File[] = [];
    const rejected: string[] = [];
    for (const file of incoming) {
      const extension = file.name.split(".").pop()?.toLowerCase();
      if (!extension || !formats.includes(extension)) rejected.push(`${file.name}: unsupported format`);
      else if (!file.size || file.size > maxFileSizeMb * 1024 * 1024) rejected.push(`${file.name}: must be between 1 byte and ${maxFileSizeMb} MB`);
      else accepted.push(file);
    }
    onFilesChange([...files, ...accepted]);
    setError(rejected.join(". "));
  }

  return <Card className="medical-uploader">
    <div className="medical-uploader-heading"><div><strong>Medical images and scanned PDFs</strong><p>Add several de-identified studies. Supported files are converted internally to model-ready images.</p></div><UploadCloud aria-hidden="true" size={22} /></div>
    <input ref={inputRef} className="sr-only" type="file" multiple accept={formats.map((format) => `.${format}`).join(",")} aria-label="Medical image files" onChange={(event) => { add(Array.from(event.target.files || [])); event.target.value = ""; }} />
    <button type="button" className={`medical-dropzone${dragging ? " is-dragging" : ""}`} onClick={() => inputRef.current?.click()} onDragEnter={(event) => { event.preventDefault(); setDragging(true); }} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={(event) => { event.preventDefault(); setDragging(false); }} onDrop={(event) => { event.preventDefault(); setDragging(false); add(Array.from(event.dataTransfer.files)); }}>
      <span className="medical-dropzone-icon"><UploadCloud aria-hidden="true" size={26} /></span>
      <span><strong>Click to upload</strong> or drag and drop multiple studies</span>
      <small>PNG, JPEG, WebP, TIFF, BMP, GIF, AVIF, JPEG 2000, PNM, PCX, TGA, ICO, DICOM, PDF · max {maxFileSizeMb} MB each</small>
    </button>
    {error && <p className="medical-upload-error" role="alert">{error}</p>}
    {files.map((file, index) => <ImageRow key={`${file.name}-${file.lastModified}-${index}`} file={file} onRemove={() => onFilesChange(files.filter((_, itemIndex) => itemIndex !== index))} />)}
  </Card>;
}

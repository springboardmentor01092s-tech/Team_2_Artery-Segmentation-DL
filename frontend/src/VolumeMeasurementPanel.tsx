import { useEffect, useRef, useState } from 'react';

type Section = {
  grid_size: number;
  step_mm: number;
  lumen_pixels_ij: number[][];
  center_ras_mm: number[];
  area_mm2: number;
  equivalent_diameter_mm: number;
};

type Candidate = {
  id: string;
  path_id: string;
  minimum_diameter_mm: number;
  reference_diameter_mm: number;
  narrowing_percent: number;
  severity: string;
  cross_sections?: Section[];
};

function SectionImage({ section, title }: { section: Section; title: string }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const context = canvas.current?.getContext('2d');
    if (!context) return;
    const pixels = context.createImageData(section.grid_size, section.grid_size);
    for (const [i, j] of section.lumen_pixels_ij) {
      const offset = (j * section.grid_size + i) * 4;
      pixels.data[offset] = 35;
      pixels.data[offset + 1] = 210;
      pixels.data[offset + 2] = 180;
      pixels.data[offset + 3] = 255;
    }
    context.putImageData(pixels, 0, 0);
  }, [section]);
  return <figure style={{ margin: 0 }}>
    <canvas ref={canvas} width={section.grid_size} height={section.grid_size}
      role="img" aria-label={`${title} sampled lumen section`}
      style={{ width: '100%', maxWidth: 280, background: '#111820', imageRendering: 'pixelated' }} />
    <figcaption>{title} · {section.area_mm2.toFixed(2)} mm² · equivalent diameter {section.equivalent_diameter_mm.toFixed(2)} mm</figcaption>
    <p>Centre RAS {section.center_ras_mm.map(value => value.toFixed(2)).join(', ')} mm · sampling {section.step_mm} mm</p>
  </figure>;
}

export default function VolumeMeasurementPanel({ candidates }: { candidates: Candidate[] }) {
  const [chosen, setChosen] = useState('');
  const selected = candidates.find(candidate => candidate.id === chosen) ?? candidates[0];
  if (!selected?.cross_sections?.length) return null;
  return <section aria-label="Candidate cross-section comparison">
    <h4>Perpendicular lumen sections</h4>
    <label>Geometry candidate <select value={selected.id} onChange={event => setChosen(event.target.value)}>
      {candidates.map(candidate => <option key={candidate.id} value={candidate.id}>{candidate.id} · {candidate.path_id}</option>)}
    </select></label>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 220px), 1fr))', gap: 20 }}>
      {selected.cross_sections.map((section, index) => <SectionImage key={`${selected.id}-${index}`} section={section}
        title={index === 0 ? 'Candidate minimum' : 'Selected reference'} />)}
    </div>
    <p>Diameter narrowing = (1 − {selected.minimum_diameter_mm.toFixed(2)} / {selected.reference_diameter_mm.toFixed(2)}) × 100 = {selected.narrowing_percent.toFixed(2)}%.</p>
    <p>Experimental category {selected.severity}. Reference selection uses the path percentile. Measurement uncertainty remains unquantified.</p>
  </section>;
}

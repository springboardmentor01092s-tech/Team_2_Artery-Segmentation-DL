import { useEffect, useRef, useState } from 'react';
import { apiUrl } from './api';
import { Button } from './components/prismui/button';

type Point = [number, number, number];
type Slice = { axis: string; coarse_index: number; artifact: string };
type MaskComponent = { id: number; foreground_voxels: number; points: Point[] };
type MaskQuality = { largestFraction: number; fragmentVoxels: number; fragmentVolumeMm3: number };
const initialView = { yaw: .5, pitch: -.25, zoom: 1 };
const turn = Math.PI / 12;
const presets = [
  { label: 'Angled', yaw: initialView.yaw, pitch: initialView.pitch, axis: null },
  { label: 'Coronal', yaw: 0, pitch: 0, axis: 'RAS Y' },
  { label: 'Sagittal', yaw: Math.PI / 2, pitch: 0, axis: 'RAS X' },
  { label: 'Axial', yaw: 0, pitch: Math.PI / 2, axis: 'RAS Z' },
];
const planeLabels: Record<string, string> = { 'RAS X': 'Sagittal', 'RAS Y': 'Coronal', 'RAS Z': 'Axial' };

export default function VolumeOrbit({ url, token, runId, shape, slices, previews }: {
  url: string; token: string; runId: string; shape: number[];
  slices: Slice[]; previews: Record<string, string>;
}) {
  const [points, setPoints] = useState<Point[] | null>(null);
  const [components, setComponents] = useState<MaskComponent[]>([]);
  const [showAllComponents, setShowAllComponents] = useState(false);
  const [foregroundVoxels, setForegroundVoxels] = useState(0);
  const [maskQuality, setMaskQuality] = useState<MaskQuality | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [view, setView] = useState(initialView);
  const [grid, setGrid] = useState(true);
  const [sliceIndex, setSliceIndex] = useState(0);
  const selectedSlice = slices[sliceIndex];
  const canvas = useRef<HTMLCanvasElement>(null);
  const pointer = useRef<{ id: number; x: number; y: number } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setPoints(null);
    setError('');
    fetch(apiUrl(url), { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal })
      .then(async response => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Unable to load the saved 3D mask.');
        const listed = (data.components || []) as MaskComponent[];
        setComponents(listed);
        setForegroundVoxels(Number(data.foreground_voxels || 0));
        setMaskQuality({
          largestFraction: Number(data.largest_component_fraction || 0),
          fragmentVoxels: Number(data.isolated_fragment_voxels || 0),
          fragmentVolumeMm3: Number(data.isolated_fragment_volume_mm3 || 0),
        });
        return (listed.length ? listed[0].points : data.points) as Point[];
      })
      .then(result => { if (!controller.signal.aborted) setPoints(result); })
      .catch(cause => { if (!controller.signal.aborted) setError(cause.message); });
    return () => controller.abort();
  }, [url, token, attempt]);

  useEffect(() => {
    if (!components.length) return;
    setPoints(showAllComponents
      ? components.flatMap(component => component.points)
      : components[0].points);
  }, [components, showAllComponents]);

  useEffect(() => {
    const element = canvas.current;
    const context = element?.getContext('2d');
    if (!element || !context || !points?.length) return;
    const draw = () => {
      const { width, height } = element.getBoundingClientRect();
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      element.width = Math.round(width * ratio);
      element.height = Math.round(height * ratio);
      context.scale(ratio, ratio);
      const scale = Math.min(width, height) * .43 * view.zoom;
      const cy = Math.cos(view.yaw), sy = Math.sin(view.yaw);
      const cp = Math.cos(view.pitch), sp = Math.sin(view.pitch);
      const project = ([x, y, z]: Point) => {
        const horizontal = cy * x + sy * y;
        const forward = -sy * x + cy * y;
        return [horizontal, cp * z - sp * forward, sp * z + cp * forward];
      };
      const position = ([x, y]: number[]) => [width / 2 + x * scale, height / 2 - y * scale] as const;
      const line = (from: Point, to: Point, color: string) => {
        context.beginPath();
        context.moveTo(...position(project(from)));
        context.lineTo(...position(project(to)));
        context.strokeStyle = color;
        context.stroke();
      };
      if (grid) {
        for (let index = -5; index <= 5; index++) {
          const offset = index / 5;
          line([offset, -1, -.95], [offset, 1, -.95], '#365367');
          line([-1, offset, -.95], [1, offset, -.95], '#365367');
        }
      }
      const projected = points.map(project);
      projected.sort((a, b) => a[2] - b[2]);
      const size = Math.max(1.5, Math.min(4.5, 3.2 * view.zoom));
      for (const [x, y, depth] of projected) {
        context.fillStyle = `hsl(188 76% ${Math.round(49 + depth * 24)}%)`;
        context.beginPath();
        context.arc(width / 2 + x * scale, height / 2 - y * scale, size / 2, 0, Math.PI * 2);
        context.fill();
      }
    };
    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(element);
    return () => observer.disconnect();
  }, [points, view, grid]);

  function rotate(yaw: number, pitch: number) {
    setView(current => ({ ...current, yaw: (current.yaw + yaw) % (2 * Math.PI),
      pitch: Math.max(-Math.PI / 2, Math.min(Math.PI / 2, current.pitch + pitch)) }));
  }

  if (error) return <div><p role="alert">{error}</p><Button type="button" onClick={() => setAttempt(value => value + 1)}>Retry viewer</Button></div>;
  if (points === null) return <p role="status">Loading the saved vessel mask…</p>;
  if (!points.length) return <p role="status">The saved mask is empty. Use the slice previews to review the run.</p>;

  return <div className="volume-orbit">
    <div className="volume-orbit-stage">
    <div className="volume-orbit-heading"><strong>Vessel viewport</strong><span>Predicted mask · Research use</span></div>
    <canvas ref={canvas} className="volume-orbit-canvas" tabIndex={0}
      aria-label="Interactive 3D vessel mask. Use arrow keys to rotate."
      onKeyDown={event => {
        switch (event.key) {
          case 'ArrowLeft': rotate(-turn, 0); break;
          case 'ArrowRight': rotate(turn, 0); break;
          case 'ArrowUp': rotate(0, turn); break;
          case 'ArrowDown': rotate(0, -turn); break;
          default: return;
        }
        event.preventDefault();
      }}
      onPointerDown={event => {
        if (event.button !== 0 || pointer.current) return;
        event.currentTarget.setPointerCapture(event.pointerId);
        pointer.current = { id: event.pointerId, x: event.clientX, y: event.clientY };
      }}
      onPointerMove={event => {
        const previous = pointer.current;
        if (!previous || previous.id !== event.pointerId) return;
        rotate((event.clientX - previous.x) * .012, (event.clientY - previous.y) * .012);
        pointer.current = { id: event.pointerId, x: event.clientX, y: event.clientY };
      }}
      onLostPointerCapture={() => { pointer.current = null; }} />
    <p className="caption">Drag or use the arrow keys to rotate. The grid is a visual guide.</p>
    </div>
    <aside className="volume-orbit-inspector" aria-label="3D workspace inspector">
    <div><h4>View controls</h4>
      <div className="volume-downloads" role="group" aria-label="View presets">
        {presets.map(preset => <Button key={preset.label} type="button"
          aria-pressed={view.yaw === preset.yaw && view.pitch === preset.pitch}
          onClick={() => {
            setView(current => ({ ...current, yaw: preset.yaw, pitch: preset.pitch }));
            const index = slices.findIndex(slice => slice.axis === preset.axis);
            if (index >= 0) setSliceIndex(index);
          }}>{preset.label}</Button>)}
      </div>
    </div>
    <div className="volume-downloads" role="group" aria-label="3D view controls">
      <Button type="button" onClick={() => rotate(-turn, 0)}>Rotate left</Button>
      <Button type="button" onClick={() => rotate(turn, 0)}>Rotate right</Button>
      <Button type="button" onClick={() => rotate(0, turn)}>Tilt up</Button>
      <Button type="button" onClick={() => rotate(0, -turn)}>Tilt down</Button>
      <Button type="button" disabled={view.zoom <= .5} onClick={() => setView(current => ({ ...current, zoom: Math.max(.5, current.zoom / 1.2) }))}>Zoom out</Button>
      <Button type="button" disabled={view.zoom >= 3} onClick={() => setView(current => ({ ...current, zoom: Math.min(3, current.zoom * 1.2) }))}>Zoom in</Button>
      <Button type="button" onClick={() => setView(initialView)}>Reset view</Button>
    </div>
    <label className="volume-confirm"><input type="checkbox" checked={grid} onChange={event => setGrid(event.target.checked)} />Show reference grid</label>
    {components.length > 1 && <section className="volume-component-quality" aria-label="Predicted mask component quality">
      <h4>Mask connectivity</h4>
      <p><strong>{components.length} disconnected components</strong> · {foregroundVoxels.toLocaleString()} source-grid foreground voxels.</p>
      <p className="caption">Largest component: {components[0].foreground_voxels.toLocaleString()} voxels
        {maskQuality ? ` (${(maskQuality.largestFraction * 100).toFixed(1)}%). Fragments: ${maskQuality.fragmentVoxels.toLocaleString()} voxels / ${maskQuality.fragmentVolumeMm3.toFixed(1)} mm³.` : '.'}</p>
      <p role="alert"><strong>Measurement withheld:</strong> disconnected predictions are not eligible for a research stenosis grade.</p>
      <label className="volume-confirm"><input type="checkbox" checked={showAllComponents}
        onChange={event => setShowAllComponents(event.target.checked)} />Show all disconnected components</label>
    </section>}
    {selectedSlice && <section aria-label="Saved slice reference">
      <h4>Slice reference</h4>
      <label>Plane<select value={sliceIndex} onChange={event => setSliceIndex(Number(event.target.value))}>
        {slices.map((slice, index) => <option key={slice.artifact} value={index}>{planeLabels[slice.axis] ?? slice.axis}</option>)}
      </select></label>
      {previews[selectedSlice.artifact] ? <img className="volume-orbit-slice" src={previews[selectedSlice.artifact]}
        alt={`Saved ${planeLabels[selectedSlice.axis] ?? selectedSlice.axis} overlay at slice ${selectedSlice.coarse_index}`} />
        : <p className="caption">Saved slice preview unavailable.</p>}
    </section>}
    <section aria-label="Saved run details">
      <h4>Saved run</h4>
      <p className="volume-orbit-run">{runId}</p>
      <p className="caption">Source grid {shape.join(' × ')} voxels. The viewport samples the predicted mask. Use the full mask download for detailed review.</p>
    </section>
    </aside>
  </div>;
}

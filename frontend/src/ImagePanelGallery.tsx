import { useEffect, useState } from 'react';
import { apiUrl, request } from './api';
import './image-panel-gallery.css';

export type ImagePanel = { key: string; title: string; description: string; available: boolean; url: string | null };

export default function ImagePanelGallery({ token, imageId, runId, modelVersion, panels }: {
  token: string; imageId: string; runId: string; modelVersion: string; panels?: ImagePanel[];
}) {
  const [items, setItems] = useState<ImagePanel[]>([]);
  const [urls, setUrls] = useState<Record<string, string>>({});
  const [failed, setFailed] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    const objects: string[] = [];
    setItems([]); setUrls({}); setFailed([]); setError(''); setLoading(true);
    async function load() {
      try {
        const inventory = panels ?? (await request<{ panels: ImagePanel[] }>(`/api/images/${imageId}/analyses/${runId}/panels`, token)).panels;
        if (!active) return;
        setItems(inventory);
        await Promise.all(inventory.filter(p => p.available && p.url).map(async p => {
          try {
            const response = await fetch(apiUrl(p.url!), { headers: { Authorization: `Bearer ${token}` } });
            if (!response.ok) throw new Error('Unavailable');
            const url = URL.createObjectURL(await response.blob());
            objects.push(url);
            if (active) setUrls(prev => ({ ...prev, [p.key]: url }));
            else URL.revokeObjectURL(url);
          } catch { if (active) setFailed(prev => [...prev, p.key]); }
        }));
      } catch { if (active) setError('Image evidence could not be loaded. Your saved analysis is unchanged.'); }
      finally { if (active) setLoading(false); }
    }
    void load();
    return () => { active = false; objects.forEach(url => URL.revokeObjectURL(url)); };
  }, [token, imageId, runId, panels, retry]);
  return <section className="image-evidence-gallery" aria-label="Image explanation panels" aria-busy={loading}>
    <h3>Image explanation & visual evidence</h3>
    <p className="caption">Run {runId} · Model {modelVersion}. Actual saved artifacts only; no illustrative reference images.</p>
    <p className="caption">Views use their recorded source or prepared coordinate frame. Landmarks are not inferred from the screenshot. Boundaries are deterministic mask contours, not anatomical verification.</p>
    {loading && <p role="status">Loading saved image panels…</p>}
    {error && <p role="alert">{error}</p>}
    {(error || failed.length > 0) && <button type="button" onClick={() => setRetry(n => n + 1)}>Retry unavailable images</button>}
    <div className="image-evidence-grid">{items.map(panel => <figure key={panel.key}>
      {urls[panel.key] && !failed.includes(panel.key) ? <a href={urls[panel.key]} target="_blank" rel="noreferrer" aria-label={`Open ${panel.title}`}><img src={urls[panel.key]} alt={panel.title} loading="lazy" onError={() => setFailed(prev => [...prev, panel.key])} /></a>
        : <div className="image-evidence-empty">{!panel.available || failed.includes(panel.key) ? 'Unavailable · no verified display artifact' : 'Loading…'}</div>}
      <figcaption><strong>{panel.title}</strong><p>{panel.description}</p></figcaption>
    </figure>)}</div>
  </section>;
}

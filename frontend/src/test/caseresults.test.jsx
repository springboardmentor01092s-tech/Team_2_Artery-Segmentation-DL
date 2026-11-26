import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import api from '../api';
import CaseResults from '../pages/CaseResults';
import { makeGet, PIPELINE } from './fixtures';

function renderResults(id = 1) {
  localStorage.setItem('token', 'test-token');
  return render(
    <MemoryRouter initialEntries={[`/cases/${id}/analysis`]}>
      <Routes>
        <Route path="/cases/:id/analysis" element={<CaseResults />} />
        <Route path="/login" element={<div>LOGIN PAGE</div>} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  api.get.mockImplementation(makeGet());
  api.post.mockResolvedValue({ data: PIPELINE });
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => PIPELINE })));
  window.URL.createObjectURL = vi.fn(() => 'blob:test');
  window.URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
});

describe('Case results page', () => {
  it('opens the saved result without running the models again', async () => {
    renderResults();
    expect(await screen.findByText('Case p001: stenosis analysis')).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('case_1_pipeline.json'));
    expect(api.post).not.toHaveBeenCalled();
  });

  it('runs the pipeline once when no saved result exists', async () => {
    fetch.mockResolvedValue({ ok: false });
    renderResults();
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/cases/1/stenosis-pipeline'));
  });

  it('shows the summary tiles for the highest-confidence region', async () => {
    renderResults();
    await screen.findByText('Case p001: stenosis analysis');
    expect((await screen.findAllByText('Mild')).length).toBeGreaterThan(0);
    expect(screen.getByText('Estimated narrowing').parentElement).toHaveTextContent('26.5%');
    expect(screen.getByText('Classifier confidence').parentElement).toHaveTextContent('0.972');
    expect(screen.getByText('Stenosis candidates').parentElement).toHaveTextContent('2');
  });

  it('lists every pipeline stage with readable names', async () => {
    renderResults();
    expect(await screen.findByText('1. Artery segmentation')).toBeInTheDocument();
    expect(screen.getByText('2. Stenosis segmentation')).toBeInTheDocument();
    expect(screen.getByText('10. Visualization')).toBeInTheDocument();
  });

  it('labels the segmentation toggle Artery and Stenosis', async () => {
    renderResults();
    await screen.findByText('Case p001: stenosis analysis');
    expect(screen.getByRole('button', { name: 'Artery' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Stenosis' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Syntax' })).not.toBeInTheDocument();
  });

  it('shows the detected regions and the explanation', async () => {
    renderResults();
    expect(await screen.findByText('Middle-center')).toBeInTheDocument();
    expect(screen.getByText('Upper-center')).toBeInTheDocument();
    expect(screen.getByText(/97\.2% confident/)).toBeInTheDocument();
  });

  it('shows the model performance and the model comparison', async () => {
    renderResults();
    expect(await screen.findByText('6. Model performance')).toBeInTheDocument();
    expect(await screen.findByText('7. Model comparison')).toBeInTheDocument();
    expect(screen.getByText('Attention U-Net (stenosis)')).toBeInTheDocument();
    expect(screen.getByText('0.4888')).toHaveClass('text-emerald-700');
  });

  it.each(['pdf', 'csv', 'json'])('downloads the %s report', async (fmt) => {
    const user = userEvent.setup();
    renderResults();
    await screen.findByText('Case p001: stenosis analysis');
    await user.click(screen.getByRole('button', { name: fmt.toUpperCase() }));
    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/cases/1/report', {
        params: { format: fmt },
        responseType: 'blob',
      })
    );
    expect(window.URL.createObjectURL).toHaveBeenCalled();
  });

  it('shows a message when the report endpoint is missing (404)', async () => {
    const base = makeGet();
    api.get.mockImplementation(async (url, cfg) => {
      if (url.endsWith('/report')) throw { response: { status: 404 } };
      return base(url, cfg);
    });
    const user = userEvent.setup();
    renderResults();
    await screen.findByText('Case p001: stenosis analysis');
    await user.click(screen.getByRole('button', { name: 'PDF' }));
    expect(await screen.findByText('The report endpoint is not available.')).toBeInTheDocument();
  });

  it('shows a message when the report cannot be built', async () => {
    const base = makeGet();
    api.get.mockImplementation(async (url, cfg) => {
      if (url.endsWith('/report')) throw { response: { status: 400 } };
      return base(url, cfg);
    });
    const user = userEvent.setup();
    renderResults();
    await screen.findByText('Case p001: stenosis analysis');
    await user.click(screen.getByRole('button', { name: 'CSV' }));
    expect(
      await screen.findByText('Could not download the report. Run the pipeline for this case first.')
    ).toBeInTheDocument();
  });

  it('re-runs the pipeline on request', async () => {
    const user = userEvent.setup();
    renderResults();
    await screen.findByText('Case p001: stenosis analysis');
    await user.click(await screen.findByRole('button', { name: 'Re-run pipeline' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/cases/1/stenosis-pipeline'));
  });

  it('explains a case without a scan and disables the downloads', async () => {
    renderResults(2);
    expect(await screen.findByText(/no scan yet/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'PDF' })).toBeDisabled();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('says so when the case does not exist', async () => {
    renderResults(99);
    expect(await screen.findByText('Case not found.')).toBeInTheDocument();
  });

  it('warns when the backend is not running', async () => {
    api.get.mockRejectedValue(new Error('Network Error'));
    renderResults();
    expect(await screen.findByText('Could not load this case. Is the backend running?')).toBeInTheDocument();
  });

  it('sends the user to the login page when the token is rejected (401)', async () => {
    api.get.mockRejectedValue({ response: { status: 401 } });
    renderResults();
    expect(await screen.findByText('LOGIN PAGE')).toBeInTheDocument();
  });
});
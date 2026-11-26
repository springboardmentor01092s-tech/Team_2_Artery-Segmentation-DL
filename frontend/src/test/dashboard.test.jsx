import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import api from '../api';
import Dashboard from '../pages/dashboard';
import { makeGet } from './fixtures';

function renderDashboard() {
  localStorage.setItem('token', 'test-token');
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/login" element={<div>LOGIN PAGE</div>} />
        <Route path="/cases/:id/analysis" element={<div>ANALYSIS PAGE</div>} />
      </Routes>
    </MemoryRouter>
  );
}

const tab = (name) => screen.getByRole('button', { name });

beforeEach(() => {
  api.get.mockImplementation(makeGet());
  api.post.mockResolvedValue({ data: {} });
  api.delete.mockResolvedValue({ data: {} });
  window.URL.createObjectURL = vi.fn(() => 'blob:test');
  window.URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
});

describe('Dashboard: cases', () => {
  it('lists the cases and the counters', async () => {
    renderDashboard();
    expect(await screen.findByText('p001')).toBeInTheDocument();
    expect(screen.getByText('p002')).toBeInTheDocument();
    expect(screen.getByText('Total cases').parentElement).toHaveTextContent('2');
    expect(screen.getByText('Awaiting analysis').parentElement).toHaveTextContent('1');
    expect(screen.getByText('With scan uploaded').parentElement).toHaveTextContent('1');
  });

  it('shows the four sections in the sidebar', async () => {
    renderDashboard();
    await screen.findByText('p001');
    for (const name of ['Cases', 'Segmentation', 'Stenosis', 'Reports']) {
      expect(tab(name)).toBeInTheDocument();
    }
  });

  it('filters cases with the search box', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('p001');
    await user.type(screen.getByPlaceholderText('Search by patient ID, gender, region...'), 'p002');
    expect(screen.queryByText('p001')).not.toBeInTheDocument();
    expect(screen.getByText('p002')).toBeInTheDocument();
  });

  it.each([
    ['clinician', true, true, true],
    ['data_scientist', false, false, true],
    ['researcher', false, false, false],
  ])('%s sees the right buttons', async (role, canCreate, canDelete, canPreprocess) => {
    api.get.mockImplementation(makeGet({ role }));
    renderDashboard();
    await screen.findByText('Test User');
    await screen.findByText('p001');
    expect(!!screen.queryByRole('button', { name: '+ New Case' })).toBe(canCreate);
    expect(!!screen.queryAllByRole('button', { name: 'Delete' }).length).toBe(canDelete);
    expect(!!screen.queryAllByRole('button', { name: 'Preprocess' }).length).toBe(canPreprocess);
  });

  it('asks for a patient ID when a new case is saved empty', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await user.click(await screen.findByRole('button', { name: '+ New Case' }));
    expect(screen.getByRole('heading', { name: 'New Case' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Create case' }));
    expect(await screen.findByText('Patient ID is required.')).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('creates a new case', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await user.click(await screen.findByRole('button', { name: '+ New Case' }));
    await user.type(screen.getByLabelText('Patient ID *'), 'p-new');
    await user.type(screen.getByLabelText('Age'), '45');
    await user.click(screen.getByRole('button', { name: 'Create case' }));
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        '/cases',
        expect.objectContaining({ patient_id: 'p-new', age: 45 })
      )
    );
  });

  it('deletes a case after confirmation', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('p001');
    await user.click(screen.getAllByRole('button', { name: 'Delete' })[0]);
    const dialog = screen.getByText('Delete case?').parentElement;
    await user.click(within(dialog).getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/cases/1'));
  });

  it('runs preprocessing and shows the stages', async () => {
    api.post.mockResolvedValueOnce({
      data: { stages: [{ name: '1_original', url: '/uploads/processed/a.png' }] },
    });
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('p001');
    await user.click(screen.getByRole('button', { name: 'Preprocess' }));
    expect(await screen.findByText('Preprocessing pipeline')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/cases/1/preprocess');
  });

  it('runs artery segmentation and shows the result window', async () => {
    api.post.mockResolvedValueOnce({
      data: {
        task: 'syntax',
        overlay_url: '/uploads/results/o.png',
        mask_url: '/uploads/results/m.png',
        foreground_percent: 3.2,
        max_probability: 0.98,
        threshold: 0.5,
        model_version: 'unet-artery-v1',
        vessel: { vessel_segments: 2, centerline_url: '/uploads/results/c.png' },
      },
    });
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('p001');
    await user.click(screen.getByRole('button', { name: 'Segment' }));
    expect(await screen.findByText('Segmentation result (Artery)')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/cases/1/segment', null, { params: { task: 'syntax' } });
  });

  it('logs out and goes to the login page', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('p001');
    await user.click(tab('Logout'));
    expect(await screen.findByText('LOGIN PAGE')).toBeInTheDocument();
    expect(localStorage.getItem('token')).toBeNull();
  });

  it('logs the user out when the token is rejected (401)', async () => {
    const base = makeGet();
    api.get.mockImplementation(async (url, cfg) => {
      if (url === '/cases' || url === '/auth/me') throw { response: { status: 401 } };
      return base(url, cfg);
    });
    renderDashboard();
    expect(await screen.findByText('LOGIN PAGE')).toBeInTheDocument();
    expect(localStorage.getItem('token')).toBeNull();
  });

  it('warns when the backend is not running', async () => {
    api.get.mockImplementation(async (url) => {
      if (url === '/auth/me') return { data: { name: 'Test User', role: 'clinician' } };
      throw new Error('Network Error');
    });
    renderDashboard();
    expect(await screen.findByText('Could not load cases. Is the backend running?')).toBeInTheDocument();
  });
});

describe('Dashboard: model comparison', () => {
  it('shows the artery model comparison in the Segmentation tab', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('p001');
    await user.click(tab('Segmentation'));

    expect(screen.getByText('Segment coronary arteries and measure vessels (artery model)')).toBeInTheDocument();
    expect(await screen.findByText(/Artery segmentation: model comparison/)).toBeInTheDocument();
    expect(screen.getByText('Attention U-Net (artery)')).toBeInTheDocument();
    expect(screen.queryByText('Attention U-Net (stenosis)')).not.toBeInTheDocument();
  });

  it('marks the best value of each column in green', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('p001');
    await user.click(tab('Segmentation'));

    expect(await screen.findByText('0.7597')).toHaveClass('text-emerald-700');
    expect(screen.getByText('0.7509')).not.toHaveClass('text-emerald-700');
    expect(screen.getByText('0.7792')).toHaveClass('text-emerald-700');
    expect(screen.getByText('0.7788')).not.toHaveClass('text-emerald-700');
  });

  it('shows the stenosis comparison and the classifier performance in the Stenosis tab', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('p001');
    await user.click(tab('Stenosis'));

    expect(await screen.findByText(/Stenosis segmentation: model comparison/)).toBeInTheDocument();
    expect(await screen.findByText(/Stenosis classifier performance/)).toBeInTheDocument();
    expect(screen.getByText('86.3%')).toBeInTheDocument();
    expect(screen.getByText(/TP 350/)).toBeInTheDocument();
  });

  it('shows a Full report button for a case with a scan in the Stenosis tab', async () => {
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('p001');
    await user.click(tab('Stenosis'));
    await user.click(await screen.findByRole('button', { name: 'Full report' }));
    expect(await screen.findByText('ANALYSIS PAGE')).toBeInTheDocument();
  });
});

describe('Dashboard: reports tab', () => {
  async function openReports(user) {
    renderDashboard();
    await screen.findByText('p001');
    await user.click(tab('Reports'));
    return screen.findAllByRole('button', { name: 'PDF' });
  }

  it('shows report buttons only for cases with a scan', async () => {
    const user = userEvent.setup();
    const pdfButtons = await openReports(user);
    expect(screen.getByText('Open or download the analysis report of a case')).toBeInTheDocument();
    expect(pdfButtons).toHaveLength(1);
    expect(screen.getAllByRole('button', { name: 'CSV' })).toHaveLength(1);
    expect(screen.getAllByRole('button', { name: 'JSON' })).toHaveLength(1);
    expect(screen.getByText('No scan uploaded')).toBeInTheDocument();
  });

  it.each(['pdf', 'csv', 'json'])('downloads the %s report through the api', async (fmt) => {
    const user = userEvent.setup();
    await openReports(user);
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
    await openReports(user);
    await user.click(screen.getByRole('button', { name: 'PDF' }));
    expect(await screen.findByText('The report endpoint is not available yet.')).toBeInTheDocument();
  });

  it('shows a message when the report cannot be built', async () => {
    const base = makeGet();
    api.get.mockImplementation(async (url, cfg) => {
      if (url.endsWith('/report')) throw { response: { status: 400 } };
      return base(url, cfg);
    });
    const user = userEvent.setup();
    await openReports(user);
    await user.click(screen.getByRole('button', { name: 'PDF' }));
    expect(
      await screen.findByText('Could not download the report. Run the stenosis pipeline for this case first.')
    ).toBeInTheDocument();
  });

  it('opens the case analysis page from the Open button', async () => {
    const user = userEvent.setup();
    await openReports(user);
    await user.click(screen.getByRole('button', { name: 'Open' }));
    expect(await screen.findByText('ANALYSIS PAGE')).toBeInTheDocument();
  });
});
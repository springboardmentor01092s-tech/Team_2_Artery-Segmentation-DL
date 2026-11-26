import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import api from '../api';
import App from '../App';
import { makeGet, PIPELINE } from './fixtures';

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  );
}

beforeEach(() => {
  api.get.mockImplementation(makeGet());
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => PIPELINE })));
});

describe('Routing and login guard', () => {
  it('sends a visitor without a token from /dashboard to the login page', async () => {
    renderAt('/dashboard');
    expect(await screen.findByText('Welcome back')).toBeInTheDocument();
  });

  it('sends a visitor without a token from a case analysis page to the login page', async () => {
    renderAt('/cases/1/analysis');
    expect(await screen.findByText('Welcome back')).toBeInTheDocument();
  });

  it('sends unknown addresses to the login page', async () => {
    renderAt('/nowhere');
    expect(await screen.findByText('Welcome back')).toBeInTheDocument();
  });

  it('shows the register page without a token', async () => {
    renderAt('/register');
    expect(await screen.findByText('Create your account')).toBeInTheDocument();
  });

  it('opens the dashboard when a token exists', async () => {
    localStorage.setItem('token', 'test-token');
    renderAt('/dashboard');
    expect(await screen.findByText('Case Management')).toBeInTheDocument();
  });

  it('opens a case analysis page when a token exists', async () => {
    localStorage.setItem('token', 'test-token');
    renderAt('/cases/1/analysis');
    expect(await screen.findByText('Case p001: stenosis analysis')).toBeInTheDocument();
  });
});
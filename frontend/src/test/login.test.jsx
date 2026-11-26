import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import api from '../api';
import Login from '../pages/login';

const EMAIL = 'doc@test.example';
const PASSWORD = 'secret-pass';

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<div>DASHBOARD PAGE</div>} />
        <Route path="/register" element={<div>REGISTER PAGE</div>} />
      </Routes>
    </MemoryRouter>
  );
}

async function fillAndSubmit(user) {
  await user.type(screen.getByPlaceholderText('you@hospital.org'), EMAIL);
  await user.type(screen.getByPlaceholderText('Enter your password'), PASSWORD);
  await user.click(screen.getByRole('button', { name: 'Sign in' }));
}

describe('Login page', () => {
  it('shows the sign-in form', () => {
    renderLogin();
    expect(screen.getByText('Welcome back')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('you@hospital.org')).toBeRequired();
    expect(screen.getByPlaceholderText('Enter your password')).toBeRequired();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
  });

  it('logs in, saves the token and opens the dashboard', async () => {
    api.post.mockResolvedValueOnce({ data: { access_token: 'tok-1' } });
    const user = userEvent.setup();
    renderLogin();
    await fillAndSubmit(user);

    expect(await screen.findByText('DASHBOARD PAGE')).toBeInTheDocument();
    expect(localStorage.getItem('token')).toBe('tok-1');
    expect(api.post).toHaveBeenCalledWith('/auth/login', { email: EMAIL, password: PASSWORD });
  });

  it('falls back to form data when the server rejects JSON (422)', async () => {
    api.post
      .mockRejectedValueOnce({ response: { status: 422 } })
      .mockResolvedValueOnce({ data: { access_token: 'tok-2' } });
    const user = userEvent.setup();
    renderLogin();
    await fillAndSubmit(user);

    expect(await screen.findByText('DASHBOARD PAGE')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledTimes(2);
    const body = api.post.mock.calls[1][1];
    expect(body).toBeInstanceOf(URLSearchParams);
    expect(body.get('username')).toBe(EMAIL);
    expect(body.get('password')).toBe(PASSWORD);
    expect(localStorage.getItem('token')).toBe('tok-2');
  });

  it('shows an error for a wrong password after the fallback (401)', async () => {
    api.post
      .mockRejectedValueOnce({ response: { status: 422 } })
      .mockRejectedValueOnce({ response: { status: 401 } });
    const user = userEvent.setup();
    renderLogin();
    await fillAndSubmit(user);

    expect(await screen.findByText('Incorrect email or password.')).toBeInTheDocument();
    expect(localStorage.getItem('token')).toBeNull();
    expect(screen.queryByText('DASHBOARD PAGE')).not.toBeInTheDocument();
  });

  it('shows an error for a direct 401', async () => {
    api.post.mockRejectedValue({ response: { status: 401 } });
    const user = userEvent.setup();
    renderLogin();
    await fillAndSubmit(user);
    expect(await screen.findByText('Incorrect email or password.')).toBeInTheDocument();
  });

  it('tells the user when the server cannot be reached', async () => {
    api.post.mockRejectedValue(new Error('Network Error'));
    const user = userEvent.setup();
    renderLogin();
    await fillAndSubmit(user);
    expect(
      await screen.findByText('Cannot reach the server. Is the backend running?')
    ).toBeInTheDocument();
  });

  it('shows a generic message for other server errors', async () => {
    api.post.mockRejectedValue({ response: { status: 500 } });
    const user = userEvent.setup();
    renderLogin();
    await fillAndSubmit(user);
    expect(await screen.findByText('Login failed. Please try again.')).toBeInTheDocument();
  });

  it('disables the button while signing in', async () => {
    api.post.mockReturnValue(new Promise(() => {}));
    const user = userEvent.setup();
    renderLogin();
    await fillAndSubmit(user);
    expect(await screen.findByRole('button', { name: 'Signing in...' })).toBeDisabled();
  });

  it('can show and hide the password', async () => {
    const user = userEvent.setup();
    renderLogin();
    const field = screen.getByPlaceholderText('Enter your password');
    expect(field).toHaveAttribute('type', 'password');
    await user.click(screen.getByRole('button', { name: 'Show' }));
    expect(field).toHaveAttribute('type', 'text');
    await user.click(screen.getByRole('button', { name: 'Hide' }));
    expect(field).toHaveAttribute('type', 'password');
  });

  it('links to the register page', async () => {
    const user = userEvent.setup();
    renderLogin();
    await user.click(screen.getByRole('link', { name: 'Create an account' }));
    expect(await screen.findByText('REGISTER PAGE')).toBeInTheDocument();
  });
});
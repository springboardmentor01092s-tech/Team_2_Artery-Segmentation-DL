import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import api from '../api';
import Register from '../pages/register';

function renderRegister() {
  return render(
    <MemoryRouter initialEntries={['/register']}>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<div>LOGIN PAGE</div>} />
      </Routes>
    </MemoryRouter>
  );
}

async function fillForm(user, { password = 'Abcdef1!', confirm = password } = {}) {
  await user.type(screen.getByPlaceholderText('Dr. Jane Smith'), 'Dr Test');
  await user.type(screen.getByPlaceholderText('you@hospital.org'), 'doc@test.example');
  await user.type(screen.getByPlaceholderText('At least 8 characters'), password);
  await user.type(screen.getByPlaceholderText('Re-enter your password'), confirm);
}

const submit = (user) => user.click(screen.getByRole('button', { name: 'Create account' }));

describe('Register page', () => {
  it('shows all fields and the four roles', () => {
    renderRegister();
    expect(screen.getByText('Create your account')).toBeInTheDocument();
    const options = within(screen.getByRole('combobox')).getAllByRole('option');
    expect(options.map((o) => o.textContent)).toEqual([
      'Radiologist / Clinician',
      'Medical Researcher',
      'Data Scientist / ML Engineer',
      'Administrator',
    ]);
  });

  it('rejects a password shorter than 8 characters', async () => {
    const user = userEvent.setup();
    renderRegister();
    await fillForm(user, { password: 'abc123' });
    await submit(user);
    expect(await screen.findByText('Password must be at least 8 characters.')).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('rejects mismatching passwords', async () => {
    const user = userEvent.setup();
    renderRegister();
    await fillForm(user, { password: 'Abcdef1!', confirm: 'Different1!' });
    await submit(user);
    expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('registers a clinician and goes to the login page', async () => {
    api.post.mockResolvedValue({ data: {} });
    const user = userEvent.setup();
    renderRegister();
    await fillForm(user);
    await submit(user);

    expect(await screen.findByText('LOGIN PAGE')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/auth/register', {
      name: 'Dr Test',
      email: 'doc@test.example',
      password: 'Abcdef1!',
      role: 'clinician',
    });
  });

  it('sends the chosen role', async () => {
    api.post.mockResolvedValue({ data: {} });
    const user = userEvent.setup();
    renderRegister();
    await user.selectOptions(screen.getByRole('combobox'), 'researcher');
    await fillForm(user);
    await submit(user);
    await screen.findByText('LOGIN PAGE');
    expect(api.post.mock.calls[0][1].role).toBe('researcher');
  });

  it('shows the server message for a duplicate email', async () => {
    api.post.mockRejectedValue({ response: { status: 400, data: { detail: 'Email already registered' } } });
    const user = userEvent.setup();
    renderRegister();
    await fillForm(user);
    await submit(user);
    expect(await screen.findByText('Email already registered')).toBeInTheDocument();
    expect(screen.queryByText('LOGIN PAGE')).not.toBeInTheDocument();
  });

  it('shows the server message when the Administrator role is chosen (backend refuses it)', async () => {
    api.post.mockRejectedValue({ response: { status: 400, data: { detail: 'Invalid role' } } });
    const user = userEvent.setup();
    renderRegister();
    await user.selectOptions(screen.getByRole('combobox'), 'admin');
    await fillForm(user);
    await submit(user);
    expect(await screen.findByText('Invalid role')).toBeInTheDocument();
  });

  it('shows a generic message when the server sends a validation list (422)', async () => {
    api.post.mockRejectedValue({ response: { status: 422, data: { detail: [{ msg: 'bad' }] } } });
    const user = userEvent.setup();
    renderRegister();
    await fillForm(user);
    await submit(user);
    expect(await screen.findByText('Please check the details you entered.')).toBeInTheDocument();
  });

  it('tells the user when the server cannot be reached', async () => {
    api.post.mockRejectedValue(new Error('Network Error'));
    const user = userEvent.setup();
    renderRegister();
    await fillForm(user);
    await submit(user);
    expect(
      await screen.findByText('Cannot reach the server. Is the backend running?')
    ).toBeInTheDocument();
  });

  it.each([
    ['abcdefgh', 'Weak'],
    ['Abcdefg1', 'Good'],
    ['Abcdef1!', 'Strong'],
  ])('rates the password %s as %s', async (password, label) => {
    const user = userEvent.setup();
    renderRegister();
    await user.type(screen.getByPlaceholderText('At least 8 characters'), password);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it('shows and hides both password fields together', async () => {
    const user = userEvent.setup();
    renderRegister();
    const a = screen.getByPlaceholderText('At least 8 characters');
    const b = screen.getByPlaceholderText('Re-enter your password');
    await user.click(screen.getByRole('button', { name: 'Show' }));
    expect(a).toHaveAttribute('type', 'text');
    expect(b).toHaveAttribute('type', 'text');
  });

  it('links to the login page', async () => {
    const user = userEvent.setup();
    renderRegister();
    await user.click(screen.getByRole('link', { name: 'Sign in' }));
    expect(await screen.findByText('LOGIN PAGE')).toBeInTheDocument();
  });
});
import { describe, expect, it } from 'vitest';
import api from '../api';

function captureRequests() {
  const seen = [];
  api.defaults.adapter = async (config) => {
    seen.push(config);
    return { data: {}, status: 200, statusText: 'OK', headers: {}, config };
  };
  return seen;
}

describe('api.js', () => {
  it('talks to the backend address', () => {
    expect(api.defaults.baseURL).toBe('http://127.0.0.1:8000');
  });

  it('sends the saved token as a Bearer header', async () => {
    localStorage.setItem('token', 'abc123');
    const seen = captureRequests();
    await api.get('/cases');
    expect(seen[0].headers.get('Authorization')).toBe('Bearer abc123');
  });

  it('sends no Authorization header when nobody is logged in', async () => {
    const seen = captureRequests();
    await api.get('/cases');
    expect(seen[0].headers.get('Authorization')).toBeUndefined();
  });

  it('reads the token on every request (after logout the header is gone)', async () => {
    const seen = captureRequests();
    localStorage.setItem('token', 'abc123');
    await api.get('/cases');
    localStorage.removeItem('token');
    await api.get('/cases');
    expect(seen[0].headers.get('Authorization')).toBe('Bearer abc123');
    expect(seen[1].headers.get('Authorization')).toBeUndefined();
  });
});
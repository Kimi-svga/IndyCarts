/**
 * Авторизация через Telegram initData.
 */

import { apiFetch, setToken } from './client';

export interface AuthResponse {
  token: string;
  telegram_id: number;
  username: string;
}

export async function authenticate(): Promise<AuthResponse | null> {
  const tg = window.Telegram?.WebApp;

  if (!tg || !tg.initData) {
    console.warn('[auth] no initData — demo mode');
    return null;
  }

  try {
    const response = await apiFetch<AuthResponse>('/api/auth/telegram', {
      method: 'POST',
      body: JSON.stringify({ init_data: tg.initData }),
    });

    setToken(response.token);
    console.log('[auth] authenticated as', response.username);

    return response;
  } catch (e) {
    const err = e as { status?: number; message?: string };

    if (err.status === 401) {
      console.error('[auth] invalid initData');
    } else if (err.status === 403) {
      console.error('[auth] subscribe to channel first');
    } else if (err.status === 404) {
      console.error('[auth] user not found — register in bot');
    } else {
      console.error('[auth] failed:', err.message);
    }

    return null;
  }
} 

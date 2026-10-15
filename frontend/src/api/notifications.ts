/**
 * API-клиент уведомлений.
 */

import { apiFetch } from './client';
import type { NotificationsResponse } from '@/types/notifications';

export async function fetchNotifications(): Promise<NotificationsResponse> {
  try {
    return await apiFetch<NotificationsResponse>('/api/notifications');
  } catch (e) {
    console.error('[notifications] fetch failed', e);
    return { items: [], unread: 0 };
  }
}

export async function markRead(notificationId: number): Promise<number> {
  try {
    const res = await apiFetch<{ ok: boolean; unread: number }>(
      '/api/notifications/read',
      {
        method: 'POST',
        body: JSON.stringify({ notification_id: notificationId }),
      },
    );
    return res.unread;
  } catch (e) {
    console.error('[notifications] markRead failed', e);
    return -1;
  }
}

export async function clearNotifications(): Promise<boolean> {
  try {
    await apiFetch('/api/notifications/clear', { method: 'DELETE' });
    return true;
  } catch (e) {
    console.error('[notifications] clear failed', e);
    return false;
  }
}

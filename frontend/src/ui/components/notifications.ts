/**
 * Bottom-sheet с уведомлениями.
 * iOS-style + Liquid Glass.
 */

import type { Notification } from '@/types/notifications';
import {
  fetchNotifications,
  markRead,
  clearNotifications,
} from '@/api/notifications';
import { showPush, ensurePushContainer } from './push';

const TYPE_HEX: Record<string, string> = {
  broadcast: '#3b82f6',
  pvp: '#f97316',
  trade: '#8b5cf6',
  clan: '#fbbf24',
  auction: '#d4a017',
  support: '#28c840',
  system: '#ef4444',
};

let overlay: HTMLElement | null = null;
let lastUnread = 0;
let pollTimer: number | null = null;

// ═══════════════════════════════════════════
// POLLING
// ═══════════════════════════════════════════

export function startNotificationPolling(intervalMs = 30000): void {
  ensurePushContainer();

  const poll = async () => {
    const data = await fetchNotifications();

    // Первый запуск — просто запоминаем
    if (lastUnread === 0 && data.unread > 0) {
      lastUnread = data.unread;
      updateBellBadge(data.unread);
      return;
    }

    // Пришло новое
    if (data.unread > lastUnread) {
      const newItems = data.items
        .filter((i) => !i.is_read)
        .slice(0, data.unread - lastUnread);

      // Показываем сверху вниз (старые → новые)
      for (const item of newItems.reverse()) {
        showPush(item, () => openNotificationsSheet());
        await sleep(200);
      }

      triggerBellShake();
      haptic('success');
    }

    lastUnread = data.unread;
    updateBellBadge(data.unread);
  };

  poll();
  pollTimer = window.setInterval(poll, intervalMs);

  // Haptic по клику на колокольчик
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) poll();
  });
}

export function stopNotificationPolling(): void {
  if (pollTimer) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
}

// ═══════════════════════════════════════════
// КОЛОКОЛЬЧИК
// ═══════════════════════════════════════════

export function updateBellBadge(unread: number): void {
  const badge = document.querySelector('.notif-dot') as HTMLElement | null;
  const btn = document.querySelector('.notif-btn') as HTMLElement | null;
  if (!badge || !btn) return;

  if (unread <= 0) {
    badge.classList.add('hidden');
    btn.classList.remove('has-unread');
    return;
  }

  badge.textContent = unread > 99 ? '99+' : String(unread);
  badge.classList.remove('hidden');
  btn.classList.add('has-unread');
}

export function triggerBellShake(): void {
  const btn = document.querySelector('.notif-btn') as HTMLElement | null;
  if (!btn) return;

  btn.classList.remove('shake');
  // reflow
  void btn.offsetWidth;
  btn.classList.add('shake');

  window.setTimeout(() => btn.classList.remove('shake'), 900);

  const badge = btn.querySelector('.notif-dot') as HTMLElement | null;
  if (badge && !badge.classList.contains('hidden')) {
    badge.classList.add('just-arrived');
    window.setTimeout(() => badge.classList.remove('just-arrived'), 700);
  }
}

// ═══════════════════════════════════════════
// BOTTOM-SHEET
// ═══════════════════════════════════════════

export async function openNotificationsSheet(): Promise<void> {
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'notif-overlay';
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeNotificationsSheet();
    });
    document.body.appendChild(overlay);
  }

  overlay.innerHTML = '<div class="notif-sheet"><div class="notif-empty"><div class="notif-empty-text">Загрузка...</div></div></div>';
  overlay.classList.add('visible');

  const data = await fetchNotifications();
  renderSheet(data.items);

  // Помечаем все как прочитанные
  for (const item of data.items) {
    if (!item.is_read) {
      await markRead(item.id);
    }
  }
  lastUnread = 0;
  updateBellBadge(0);
}

export function closeNotificationsSheet(): void {
  if (!overlay) return;
  overlay.classList.remove('visible');
}

function renderSheet(items: Notification[]): void {
  if (!overlay) return;

  const listHtml = items.length === 0
    ? `
      <div class="notif-empty">
        <iconify-icon icon="lucide:bell-off" width="48" height="48"></iconify-icon>
        <div class="notif-empty-text">Уведомлений нет</div>
        <div class="notif-empty-sub">Всё спокойно на трассе</div>
      </div>
    `
    : items.map((n) => renderItem(n)).join('');

  overlay.innerHTML = `
    <div class="notif-sheet">
      <div class="notif-handle"></div>
      <div class="notif-header">
        <div class="notif-header-title">
          <iconify-icon icon="lucide:bell" width="20" height="20"></iconify-icon>
          Уведомления
        </div>
        <button class="notif-clear-btn" id="notif-clear">Очистить</button>
      </div>
      <div class="notif-list">${listHtml}</div>
    </div>
  `;

  // Клики по карточкам
  overlay.querySelectorAll<HTMLElement>('[data-notif-id]').forEach((el) => {
    el.addEventListener('click', async () => {
      const id = Number(el.dataset.notifId);
      if (!id) return;
      el.classList.add('read');
      await markRead(id);
    });
  });

  // Кнопка «Очистить»
  const clearBtn = overlay.querySelector('#notif-clear');
  clearBtn?.addEventListener('click', async (e) => {
    e.stopPropagation();
    const ok = await clearNotifications();
    if (ok) {
      lastUnread = 0;
      updateBellBadge(0);
      renderSheet([]);
    }
  });
}

function renderItem(n: Notification): string {
  const color = TYPE_HEX[n.type] ?? '#3b82f6';
  const readClass = n.is_read ? 'read' : '';
  const timeStr = relativeTime(n.created_at);

  return `
    <div class="notif-item notif-type-${escapeAttr(n.type)} ${readClass}" data-notif-id="${n.id}">
      <div class="notif-item-bar" style="color: ${color}"></div>
      <div class="notif-item-icon" style="color: ${color}">
        <iconify-icon icon="lucide:${escapeAttr(n.icon)}" width="18" height="18"></iconify-icon>
      </div>
      <div class="notif-item-body">
        <div class="notif-item-title">${escapeHtml(n.title)}</div>
        <div class="notif-item-text">${escapeHtml(n.text)}</div>
        <div class="notif-item-time">${timeStr}</div>
      </div>
    </div>
  `;
}

// ═══════════════════════════════════════════
// УТИЛИТЫ
// ═══════════════════════════════════════════

function relativeTime(iso: string): string {
  const now = Date.now();
  const t = new Date(iso).getTime();
  const diff = Math.floor((now - t) / 1000);

  if (diff < 60) return 'только что';
  if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`;
  return `${Math.floor(diff / 86400)} д назад`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escapeAttr(text: string): string {
  return text.replace(/[^a-z0-9-]/gi, '');
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => window.setTimeout(r, ms));
}

function haptic(type: 'success' | 'warning' | 'error'): void {
  try {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred(type);
  } catch {
    // ignore
  }
}

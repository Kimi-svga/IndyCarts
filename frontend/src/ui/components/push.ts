/**
 * iOS-style push-баннер.
 * Liquid Glass.
 */

import type { Notification } from '@/types/notifications';

const MAX_STACK = 3;

// Цвета по типу (совпадают с CSS)
const TYPE_HEX: Record<string, string> = {
  broadcast: '#3b82f6',
  pvp: '#f97316',
  trade: '#8b5cf6',
  clan: '#fbbf24',
  auction: '#d4a017',
  support: '#28c840',
  system: '#ef4444',
};

export function ensurePushContainer(): HTMLElement {
  let container = document.getElementById('push-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'push-container';
    document.body.appendChild(container);
  }
  return container;
}

export function showPush(
  notif: Notification,
  onClick?: () => void,
): void {
  const container = ensurePushContainer();

  // Ограничение стека
  while (container.children.length >= MAX_STACK) {
    const first = container.firstElementChild as HTMLElement | null;
    first?.remove();
  }

  const color = TYPE_HEX[notif.type] ?? '#3b82f6';

  const el = document.createElement('div');
  el.className = 'push-banner';
  el.innerHTML = `
    <div class="push-icon" style="color: ${color}">
      <iconify-icon icon="lucide:${escapeAttr(notif.icon)}" width="20" height="20"></iconify-icon>
    </div>
    <div class="push-body">
      <div class="push-title">${escapeHtml(notif.title)}</div>
      <div class="push-text">${escapeHtml(notif.text)}</div>
    </div>
    <div class="push-time">сейчас</div>
  `;

  container.appendChild(el);

  // Появление
  requestAnimationFrame(() => {
    el.classList.add('visible');
  });

  // Клик → открыть sheet
  el.addEventListener('click', () => {
    if (onClick) onClick();
    dismiss();
  });

  // Свайп вверх
  let startY = 0;
  let moved = false;
  el.addEventListener('touchstart', (e) => {
    startY = e.touches[0].clientY;
    moved = false;
  });
  el.addEventListener('touchmove', (e) => {
    const dy = e.touches[0].clientY - startY;
    if (dy < -10) {
      moved = true;
      el.style.transform = `translateY(${Math.max(dy, -120)}px)`;
      el.style.opacity = String(Math.max(0, 1 + dy / 100));
    }
  });
  el.addEventListener('touchend', (e) => {
    const dy = e.changedTouches[0].clientY - startY;
    if (dy < -40) {
      dismiss();
    } else {
      el.style.transform = '';
      el.style.opacity = '';
    }
  });

  // Автозакрытие
  const timer = window.setTimeout(dismiss, 4000);

  function dismiss() {
    window.clearTimeout(timer);
    el.classList.add('dismissing');
    el.classList.remove('visible');
    window.setTimeout(() => el.remove(), 350);
  }
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

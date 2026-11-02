/**
 * Бейджи — иконки + модалка с описанием.
 * v2.0
 */

import { Modal } from './modal';

export type BadgeType = 'team' | 'plus' | 'trader' | 'admin';

export interface BadgeInfo {
  title: string;
  desc: string;
  icon: string;
  color: string;
}

export const BADGE_INFO: Record<BadgeType, BadgeInfo> = {
  team: {
    title: 'Команда проекта',
    desc: 'Официальный аккаунт. Часть команды Visual Merge.',
    icon: 'lucide:badge-check',
    color: 'var(--blue)',
  },
  plus: {
    title: 'Indy+ Подписка',
    desc: 'Подписчик Indy+. Максимальные бонусы в игре.',
    icon: 'lucide:gem',
    color: 'var(--purple)',
  },
  trader: {
    title: 'Трейдер',
    desc: 'Надёжный игрок. Trust Score ≥ 100.',
    icon: 'lucide:handshake',
    color: 'var(--green)',
  },
  admin: {
    title: 'Администратор',
    desc: 'Управляет игрой. Используй осторожно.',
    icon: 'lucide:shield-check',
    color: 'var(--accent)',
  },
};

/** Отрисовать иконку бейджа (для вставки в DOM). */
export function renderBadgeIcon(type: BadgeType, size = 16): HTMLButtonElement {
  const info = BADGE_INFO[type];
  const btn = document.createElement('button');
  btn.className = 'menu-badge';
  btn.type = 'button';
  btn.dataset.badge = type;
  btn.innerHTML = `<iconify-icon icon="${info.icon}" width="${size}" height="${size}" style="color: ${info.color};"></iconify-icon>`;
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    showBadgeModal(type);
  });
  return btn;
}

/** Модалка с описанием бейджа. */
export function showBadgeModal(type: BadgeType): void {
  const info = BADGE_INFO[type];
  const modal = new Modal();

  modal.show(`
    <div style="text-align: center;">
      <div class="badge-modal-icon" style="background: color-mix(in srgb, ${info.color} 15%, transparent); color: ${info.color};">
        <iconify-icon icon="${info.icon}" width="32" height="32"></iconify-icon>
      </div>
      <div class="badge-modal-title">${info.title}</div>
      <div class="badge-modal-desc">${info.desc}</div>
      <button class="modal-action default" id="badge-close" style="width: 100%;">
        Понятно
      </button>
    </div>
  `);

  document.getElementById('badge-close')?.addEventListener('click', () => modal.close());
}

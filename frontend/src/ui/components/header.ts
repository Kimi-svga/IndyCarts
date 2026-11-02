/**
 * Header — логотип + поиск + уведомления + шестерёнка + терминал.
 * v2.0
 */

import type { Router } from '../router';
import { SettingsModal } from '@/settings/modal';
import { openNotificationsSheet } from './notifications';
import { openSearchModal } from './search';

export function createHeader(router: Router): HTMLElement {
  const header = document.createElement('div');
  header.className = 'app-header';

  header.innerHTML = `
    <div class="app-header-title">
      VISUAL <span>MERGE</span>
    </div>
    <button class="app-header-btn" data-action="search" title="Поиск игрока">
      <iconify-icon icon="lucide:search" width="18" height="18"></iconify-icon>
    </button>
    <button class="app-header-btn notif-btn" data-action="notifications" title="Уведомления">
      <iconify-icon icon="lucide:bell" width="18" height="18"></iconify-icon>
      <span class="notif-dot hidden" id="notif-dot">0</span>
    </button>
    <button class="app-header-btn" data-action="settings" title="Настройки">
      <iconify-icon icon="lucide:settings" width="18" height="18"></iconify-icon>
    </button>
    <button class="app-header-btn" data-action="terminal" title="Admin">
      <iconify-icon icon="lucide:terminal" width="18" height="18"></iconify-icon>
    </button>
  `;

  const modal = new SettingsModal();

  header
    .querySelector('[data-action="search"]')
    ?.addEventListener('click', () => {
      openSearchModal((username) => {
        const openPlayer = (window as unknown as {
          __vm_open_player?: (u: string) => void;
        }).__vm_open_player;
        if (openPlayer) {
          openPlayer(username);
        } else {
          console.warn('[header] openPlayerProfile not registered');
        }
      });
    });

  header
    .querySelector('[data-action="notifications"]')
    ?.addEventListener('click', () => {
      void openNotificationsSheet();
    });

  header
    .querySelector('[data-action="settings"]')
    ?.addEventListener('click', () => {
      modal.open();
    });

  header
    .querySelector('[data-action="terminal"]')
    ?.addEventListener('click', () => {
      void router.navigate('terminal');
    });

  return header;
}

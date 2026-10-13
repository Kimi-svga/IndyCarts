/**
 * Header с логотипом + иконка админки.
 */

import type { Router } from '../router';

export function createHeader(router: Router): HTMLElement {
  const header = document.createElement('div');
  header.className = 'app-header';

  header.innerHTML = `
    <div class="app-header-title">
      VISUAL <span>MERGE</span>
    </div>
    <button class="app-header-btn" data-action="terminal" title="Admin">
      <iconify-icon icon="lucide:terminal" width="18" height="18"></iconify-icon>
    </button>
  `;

  header
    .querySelector('[data-action="terminal"]')
    ?.addEventListener('click', () => {
      void router.navigate('terminal');
    });

  return header;
} 

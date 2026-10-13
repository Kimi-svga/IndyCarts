/**
 * Bottom navigation — 5 кнопок.
 */

import type { Router, ScreenName } from '../router';

interface NavItem {
  name: ScreenName;
  icon: string;
  label: string;
}

const ITEMS: NavItem[] = [
  { name: 'menu', icon: 'lucide:flag', label: 'МЕНЮ' },
  { name: 'collection', icon: 'lucide:layers', label: 'КАРТЫ' },
  { name: 'drop', icon: 'lucide:gift', label: 'ДРОП' },
  { name: 'market', icon: 'lucide:trending-up', label: 'БИРЖА' },
  { name: 'profile', icon: 'lucide:user', label: 'ПРОФИЛЬ' },
];

export function createBottomNav(router: Router): HTMLElement {
  const nav = document.createElement('div');
  nav.className = 'app-bottom-nav';

  for (const item of ITEMS) {
    const btn = document.createElement('button');
    btn.className = 'app-nav-item';
    btn.dataset.nav = item.name;
    btn.innerHTML = `
      <iconify-icon icon="${item.icon}" width="20" height="20"></iconify-icon>
      <div class="app-nav-label">${item.label}</div>
    `;

    btn.addEventListener('click', () => {
      void router.navigate(item.name);
    });

    nav.appendChild(btn);
  }

  return nav;
}

export function updateBottomNav(active: ScreenName | null): void {
  document.querySelectorAll('.app-nav-item').forEach((el) => {
    const nav = (el as HTMLElement).dataset.nav;
    el.classList.toggle('active', nav === active);
  });
}

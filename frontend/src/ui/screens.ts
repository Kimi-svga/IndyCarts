/**
 * Главное меню — 12 кнопок.
 */

import type { Router, ScreenName } from '../router';

interface MenuItem {
  screen: ScreenName;
  icon: string;
  label: string;
}

const ITEMS: MenuItem[] = [
  { screen: 'profile', icon: 'lucide:user', label: 'Профиль' },
  { screen: 'collection', icon: 'lucide:layers', label: 'Карты' },
  { screen: 'drop', icon: 'lucide:gift', label: 'Дроп' },
  { screen: 'market', icon: 'lucide:trending-up', label: 'Биржа' },
  { screen: 'market', icon: 'lucide:target', label: 'Аукцион' },
  { screen: 'market', icon: 'lucide:shopping-cart', label: 'Магазин' },
  { screen: 'menu', icon: 'lucide:swords', label: 'PvP' },
  { screen: 'menu', icon: 'lucide:landmark', label: 'Банк' },
  { screen: 'menu', icon: 'lucide:shield', label: 'Кланы' },
  { screen: 'menu', icon: 'lucide:trophy', label: 'Рейтинг' },
  { screen: 'menu', icon: 'lucide:users', label: 'Рефералка' },
  { screen: 'menu', icon: 'lucide:gem', label: 'Indy+' },
];

export function renderMenu(
  container: HTMLElement,
  router: Router,
  userData: { username: string; balance: number; pvpRating: number } | null,
): void {
  const username = userData?.username ?? 'Гость';
  const balance = userData?.balance ?? 0;
  const pvp = userData?.pvpRating ?? 0;

  const top = document.createElement('div');
  top.className = 'menu-top';
  top.innerHTML = `
    <div class="menu-hero">
      <div class="menu-username">${escapeHtml(username)}</div>
      <div class="menu-subtitle">IndyCarts Player</div>
    </div>
    <div class="menu-stats">
      <div class="menu-stat">
        <div class="menu-stat-value">${balance.toLocaleString('ru-RU')}</div>
        <div class="menu-stat-label">Монеты</div>
      </div>
      <div class="menu-stat">
        <div class="menu-stat-value">${pvp}</div>
        <div class="menu-stat-label">Рейтинг</div>
      </div>
      <div class="menu-stat">
        <div class="menu-stat-value">—</div>
        <div class="menu-stat-label">Сезон</div>
      </div>
    </div>
  `;
  container.appendChild(top);

  const grid = document.createElement('div');
  grid.className = 'menu-grid';

  for (const item of ITEMS) {
    const btn = document.createElement('button');
    btn.className = 'menu-item';
    btn.innerHTML = `
      <iconify-icon icon="${item.icon}" width="26" height="26"></iconify-icon>
      <div class="menu-label">${item.label}</div>
    `;

    btn.addEventListener('click', () => {
      void router.navigate(item.screen);
    });

    grid.appendChild(btn);
  }

  container.appendChild(grid);
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

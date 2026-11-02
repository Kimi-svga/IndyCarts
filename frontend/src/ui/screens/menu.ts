/**
 * Главное меню — hero + 12 кнопок + Indy+ баннер.
 * v2.0
 */

import type { Router, ScreenName } from '../router';
import { renderBadgeIcon, type BadgeType } from '../components/badges';

export interface MenuUser {
  username: string;
  balance: number;
  pvpRating: number;
  badges?: string[];
  customTitle?: string | null;
  plusTier?: string;
}

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
  { screen: 'auction', icon: 'lucide:target', label: 'Аукцион' },
  { screen: 'shop', icon: 'lucide:shopping-cart', label: 'Магазин' },
  { screen: 'pvp', icon: 'lucide:swords', label: 'PvP' },
  { screen: 'bank', icon: 'lucide:landmark', label: 'Банк' },
  { screen: 'clan', icon: 'lucide:shield', label: 'Кланы' },
  { screen: 'rating', icon: 'lucide:trophy', label: 'Рейтинг' },
  { screen: 'ref', icon: 'lucide:users', label: 'Рефералка' },
  { screen: 'plus', icon: 'lucide:gem', label: 'Indy+' },
];

export function renderMenu(
  container: HTMLElement,
  router: Router,
  user: MenuUser | null,
): void {
  // ─── 1. HERO ───
  const hero = document.createElement('div');
  hero.className = 'menu-hero';

  const username = user?.username ?? 'Гость';
  const balance = user?.balance ?? 0;
  const firstLetter = username[0]?.toUpperCase() ?? '?';
  const badges = (user?.badges ?? []).filter(isBadgeType);

  hero.innerHTML = `
    <div class="menu-avatar">${escapeHtml(firstLetter)}</div>
    <div class="menu-hero-info">
      <div class="menu-hero-username-row">
        <div class="menu-hero-username">@${escapeHtml(username)}</div>
      </div>
      <div class="menu-hero-title">${escapeHtml(user?.customTitle ?? 'PLAYER')}</div>
    </div>
    <div class="menu-hero-balance">
      <div class="menu-hero-balance-value">${balance.toLocaleString('ru-RU')}</div>
      <div class="menu-hero-balance-label">Монеты</div>
    </div>
  `;

  // Добавляем бейджи в строку с ником
  const usernameRow = hero.querySelector('.menu-hero-username-row');
  if (usernameRow && badges.length > 0) {
    const badgesWrap = document.createElement('div');
    badgesWrap.className = 'menu-hero-badges';
    for (const b of badges) {
      badgesWrap.appendChild(renderBadgeIcon(b, 16));
    }
    usernameRow.appendChild(badgesWrap);
  }

  container.appendChild(hero);

  // ─── 2. СЕТКА 3×4 ───
  const grid = document.createElement('div');
  grid.className = 'menu-grid';

  for (const item of ITEMS) {
    const btn = document.createElement('button');
    btn.className = 'menu-item';
    btn.type = 'button';
    btn.innerHTML = `
      <iconify-icon icon="${item.icon}" width="24" height="24"></iconify-icon>
      <div class="menu-label">${item.label}</div>
    `;
    btn.addEventListener('click', () => {
      void router.navigate(item.screen);
    });
    grid.appendChild(btn);
  }

  container.appendChild(grid);

  // ─── 3. INDY+ БАННЕР ───
  const plusBanner = document.createElement('div');
  plusBanner.className = 'menu-plus-banner';
  plusBanner.innerHTML = `
    <div class="menu-plus-icon">
      <iconify-icon icon="lucide:gem" width="24" height="24"></iconify-icon>
    </div>
    <div class="menu-plus-body">
      <div class="menu-plus-title">Indy+</div>
      <div class="menu-plus-sub">+5 попыток в день и бонусы</div>
    </div>
    <iconify-icon icon="lucide:chevron-right" width="18" height="18" style="color: var(--text-mute);"></iconify-icon>
  `;
  plusBanner.addEventListener('click', () => {
    void router.navigate('plus');
  });
  container.appendChild(plusBanner);
}

function isBadgeType(value: string): value is BadgeType {
  return value === 'team' || value === 'plus' || value === 'trader' || value === 'admin';
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
   } 

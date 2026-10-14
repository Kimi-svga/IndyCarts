/**
 * Visual Merge — точка входа.
 * Design by Expo
 */

import './styles/global.css';
import './styles/terminal.css';
import './styles/app.css';
import './styles/settings.css';

import { Terminal } from '@/core/terminal';
import { authenticate } from '@/api/auth';
import { createApiRepo } from '@/api/repo';
import { apiFetch } from '@/api/client';
import { applySettings, loadSettings } from '@/settings/store';

import { Router } from '@/ui/router';
import { createHeader } from '@/ui/components/header';
import { createBottomNav, updateBottomNav } from '@/ui/components/bottom-nav';
import { renderMenu } from '@/ui/screens/menu';
import { renderProfile } from '@/ui/screens/profile';
import { renderCollection } from '@/ui/screens/collection';
import { renderDrop } from '@/ui/screens/drop';
import { renderMarket } from '@/ui/screens/market';
import { renderPvp } from '@/ui/screens/pvp';
import { renderBank } from '@/ui/screens/bank';
import { renderShop } from '@/ui/screens/shop';
import { renderRating } from '@/ui/screens/rating';
import { renderClan } from '@/ui/screens/clan';
import { renderAuction } from '@/ui/screens/auction';
import { renderTerminal } from '@/ui/screens/terminal';

interface MeData {
  telegram_id: number;
  username: string;
  balance: number;
  cards_count: number;
  collection_value: number;
  pvp_rating: number;
  pvp_wins: number;
  pvp_losses: number;
  daily_streak: number;
  trust_score: number;
  daily_attempts: number;
  plus_tier: string;
  plus_expires_at: string | null;
  ban_level: string;
}

const app = document.getElementById('app');
if (!app) {
  throw new Error('#app not found');
}

// ─── Применяем настройки СРАЗУ ───
applySettings(loadSettings());

// Системная тема — следим
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  const s = loadSettings();
  if (s.theme === 'system') applySettings(s);
});

if (window.Telegram?.WebApp) {
  window.Telegram.WebApp.ready();
  window.Telegram.WebApp.expand();
}

let meData: MeData | null = null;

const screenContainer = document.createElement('div');
screenContainer.className = 'app-screen-container';

const router = new Router(screenContainer);

const header = createHeader(router);
app.appendChild(header);
app.appendChild(screenContainer);

const bottomNav = createBottomNav(router);
app.appendChild(bottomNav);

const credit = document.createElement('div');
credit.className = 'design-credit';
credit.textContent = 'Design by Expo';
app.appendChild(credit);

// ─── Роуты ───

router.register('menu', (el) => {
  const menuData = meData
    ? { username: meData.username, balance: meData.balance, pvpRating: meData.pvp_rating }
    : null;
  renderMenu(el, router, menuData);
  updateBottomNav('menu');
});

router.register('profile', (el) => {
  renderProfile(el, meData);
  updateBottomNav('profile');
});

router.register('collection', async (el) => {
  await renderCollection(el);
  updateBottomNav('collection');
});

router.register('drop', (el) => {
  renderDrop(el);
  updateBottomNav('drop');
});

router.register('market', async (el) => {
  await renderMarket(el);
  updateBottomNav('market');
});

router.register('pvp', async (el) => {
  await renderPvp(el);
  updateBottomNav(null);
});

router.register('bank', async (el) => {
  await renderBank(el);
  updateBottomNav(null);
});

router.register('shop', async (el) => {
  await renderShop(el);
  updateBottomNav(null);
});

router.register('rating', async (el) => {
  await renderRating(el);
  updateBottomNav(null);
});

router.register('clan', async (el) => {
  await renderClan(el);
  updateBottomNav(null);
});

router.register('auction', async (el) => {
  await renderAuction(el);
  updateBottomNav(null);
});

router.register('terminal', (el) => {
  renderTerminal(el);
  updateBottomNav(null);
});

// ─── Заглушки ───

router.register('ref', (el) => {
  el.innerHTML = `
    <div class="empty-state">
      <iconify-icon icon="lucide:users" width="64" height="64"></iconify-icon>
      <div class="empty-text">РЕФЕРАЛКА</div>
      <div class="empty-sub">Скоро</div>
    </div>
  `;
});

router.register('plus', (el) => {
  el.innerHTML = `
    <div class="empty-state">
      <iconify-icon icon="lucide:gem" width="64" height="64"></iconify-icon>
      <div class="empty-text">INDY+</div>
      <div class="empty-sub">Открой бота → /plus</div>
    </div>
  `;
});

// ─── Auth ───

(async () => {
  const authResult = await authenticate();

  if (authResult) {
    try {
      meData = await apiFetch<MeData>('/api/me');
    } catch (e) {
      console.error('[main] failed to load /api/me', e);
    }

    const repo = createApiRepo();
    const tempContainer = document.createElement('div');
    const globalTerminal = new Terminal(tempContainer, {});
    globalTerminal.setContext({
      repo,
      print: (html: string) => globalTerminal.print(html),
      user: {
        telegramId: authResult.telegram_id,
        username: authResult.username,
        role: 'owner',
      },
    });

    (window as unknown as { __vm_terminal?: Terminal }).__vm_terminal = globalTerminal;
  }

  await router.navigate('menu');
})();

const originalNavigate = router.navigate.bind(router);
router.navigate = async (name) => {
  await originalNavigate(name);
  updateBottomNav(name);
}; 

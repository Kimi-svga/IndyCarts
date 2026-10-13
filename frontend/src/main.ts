/**
 * Visual Merge — точка входа.
 * Design by Expo
 */

import './styles/global.css';
import './styles/terminal.css';
import './styles/app.css';

import { Terminal } from '@/core/terminal';
import { authenticate } from '@/api/auth';
import { createApiRepo } from '@/api/repo';
import { apiFetch } from '@/api/client';

import { Router } from '@/ui/router';
import { createHeader } from '@/ui/components/header';
import { createBottomNav, updateBottomNav } from '@/ui/components/bottom-nav';
import { renderMenu } from '@/ui/screens/menu';
import { renderProfile } from '@/ui/screens/profile';
import { renderCollection } from '@/ui/screens/collection';
import { renderDrop } from '@/ui/screens/drop';
import { renderMarket } from '@/ui/screens/market';
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

if (window.Telegram?.WebApp) {
  window.Telegram.WebApp.ready();
  window.Telegram.WebApp.expand();
  window.Telegram.WebApp.setHeaderColor('#0a0a0a');
  window.Telegram.WebApp.setBackgroundColor('#0a0a0a');
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
    ? {
        username: meData.username,
        balance: meData.balance,
        pvpRating: meData.pvp_rating,
      }
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

router.register('market', (el) => {
  renderMarket(el);
  updateBottomNav('market');
});

router.register('terminal', (el) => {
  renderTerminal(el);
  updateBottomNav(null);
});

// ─── Auth + стартовый экран ───
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

    (window as unknown as { __vm_terminal?: Terminal }).__vm_terminal =
      globalTerminal;
  }

  await router.navigate('menu');
})();

// Обновление bottom-nav при навигации
const originalNavigate = router.navigate.bind(router);
router.navigate = async (name) => {
  await originalNavigate(name);
  updateBottomNav(name);
};

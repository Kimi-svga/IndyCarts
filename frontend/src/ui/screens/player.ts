/**
 * Профиль чужого игрока.
 * v2.0
 */

import { apiFetch } from '@/api/client';
import { BADGE_INFO, type BadgeType, showBadgeModal } from '../components/badges';

interface PlayerCard {
  id: number;
  name: string;
  rarity: string;
  image_url: string | null;
  price: number;
}

interface PlayerProfile {
  telegram_id: number;
  username: string;
  balance: number;
  pvp_rating: number;
  pvp_wins: number;
  pvp_losses: number;
  daily_streak: number;
  cards_count: number;
  collection_value: number;
  clan: { tag: string; name: string; level: number; role: string } | null;
  badges: string[];
  is_friend: boolean;
  pinned_cards: PlayerCard[];
}

export async function renderPlayer(
  container: HTMLElement,
  username: string,
  onBack: () => void,
): Promise<void> {
  // ─── Header (назад) ───
  const topBar = document.createElement('div');
  topBar.className = 'top-bar';
  topBar.innerHTML = `
    <button class="back-btn" id="player-back">
      <iconify-icon icon="lucide:arrow-left" width="20" height="20"></iconify-icon>
    </button>
    <div class="top-title">Профиль</div>
    <div style="width: 20px;"></div>
  `;
  container.appendChild(topBar);
  topBar.querySelector('#player-back')?.addEventListener('click', onBack);

  // ─── Загрузка ───
  const content = document.createElement('div');
  content.innerHTML = '<div class="empty-state">Загрузка...</div>';
  container.appendChild(content);

  let profile: PlayerProfile | null = null;
  try {
    profile = await apiFetch<PlayerProfile>(`/api/user/${encodeURIComponent(username)}`);
  } catch (e) {
    const err = e as { message?: string; status?: number };
    content.innerHTML = `
      <div class="empty-state">
        <iconify-icon icon="lucide:user-x" width="48" height="48"></iconify-icon>
        <div class="empty-text">${err.status === 404 ? 'Игрок не найден' : 'Ошибка загрузки'}</div>
        <div class="empty-sub">${escapeHtml(err.message ?? '')}</div>
      </div>
    `;
    return;
  }

  const badges = (profile.badges ?? []).filter(isBadgeType);
  const firstLetter = profile.username[0]?.toUpperCase() ?? '?';
  const kdRatio = profile.pvp_losses > 0
    ? (profile.pvp_wins / profile.pvp_losses).toFixed(2)
    : String(profile.pvp_wins);

  // ─── Hero ───
  const hero = document.createElement('div');
  hero.className = 'profile-hero';
  hero.innerHTML = `
    <div class="profile-avatar">${escapeHtml(firstLetter)}</div>
    <div class="profile-username-row">
      <div class="profile-username">@${escapeHtml(profile.username)}</div>
      <div class="profile-badges" id="profile-badges"></div>
    </div>
    ${profile.clan ? `
      <div class="profile-clan">
        🏰 [${escapeHtml(profile.clan.tag)}] ${escapeHtml(profile.clan.name)}
      </div>
    ` : ''}
  `;
  content.innerHTML = '';
  content.appendChild(hero);

  // Бейджи
  const badgesWrap = hero.querySelector('#profile-badges');
  if (badgesWrap && badges.length > 0) {
    for (const b of badges) {
      const info = BADGE_INFO[b];
      const btn = document.createElement('button');
      btn.className = 'menu-badge';
      btn.type = 'button';
      btn.innerHTML = `<iconify-icon icon="${info.icon}" width="18" height="18" style="color: ${info.color};"></iconify-icon>`;
      btn.addEventListener('click', () => showBadgeModal(b));
      badgesWrap.appendChild(btn);
    }
  }

  // ─── Статы ───
  const stats = document.createElement('div');
  stats.className = 'profile-stats';
  stats.innerHTML = `
    <div class="profile-stat">
      <div class="profile-stat-value">${profile.cards_count}</div>
      <div class="profile-stat-label">Карт</div>
    </div>
    <div class="profile-stat">
      <div class="profile-stat-value gold">${formatMoney(profile.collection_value)}</div>
      <div class="profile-stat-label">Коллекция</div>
    </div>
    <div class="profile-stat">
      <div class="profile-stat-value blue">${profile.pvp_rating}</div>
      <div class="profile-stat-label">PvP</div>
    </div>
  `;
  content.appendChild(stats);

  // ─── Доп. инфо ───
  const info = document.createElement('div');
  info.className = 'info-card';
  info.innerHTML = `
    <div class="info-row">
      <span class="info-row-label">PvP W/L</span>
      <span class="info-row-value">${profile.pvp_wins} / ${profile.pvp_losses} (${kdRatio})</span>
    </div>
    <div class="info-row">
      <span class="info-row-label">Стрик</span>
      <span class="info-row-value yellow">${profile.daily_streak} дн.</span>
    </div>
    ${profile.is_friend ? `
      <div class="info-row">
        <span class="info-row-label">Друг</span>
        <span class="info-row-value green">✅ В друзьях</span>
      </div>
    ` : ''}
  `;
  content.appendChild(info);

  // ─── Действия ───
  const actions = document.createElement('div');
  actions.className = 'profile-actions';
  actions.innerHTML = `
    <button class="btn btn-primary" id="player-friend" ${profile.is_friend ? 'disabled' : ''}>
      <iconify-icon icon="lucide:user-plus" width="16" height="16"></iconify-icon>
      ${profile.is_friend ? 'В друзьях' : 'В друзья'}
    </button>
    <button class="btn btn-secondary" id="player-pvp">
      <iconify-icon icon="lucide:swords" width="16" height="16"></iconify-icon>
      Вызвать на PvP
    </button>
  `;
  content.appendChild(actions);

  // ─── Витрина ───
  if (profile.pinned_cards.length > 0) {
    const showcaseTitle = document.createElement('div');
    showcaseTitle.className = 'profile-showcase-title';
    showcaseTitle.textContent = 'Витрина';
    content.appendChild(showcaseTitle);

    const showcase = document.createElement('div');
    showcase.className = 'profile-showcase';
    for (const card of profile.pinned_cards) {
      const el = document.createElement('div');
      el.className = `card-item ${card.rarity}`;
      el.innerHTML = `
        <div class="card-image">
          ${card.image_url
            ? `<img src="${card.image_url}" alt="${escapeHtml(card.name)}" loading="lazy" />`
            : '<iconify-icon icon="lucide:car" width="32" height="32"></iconify-icon>'}
        </div>
        <div class="card-info">
          <div class="card-name">${escapeHtml(card.name)}</div>
          <div class="card-meta">
            <span>${card.rarity.toUpperCase()}</span>
            <span class="card-price">${formatMoney(card.price)}</span>
          </div>
        </div>
      `;
      showcase.appendChild(el);
    }
    content.appendChild(showcase);
  }

  // ─── Обработчики ───
  document.getElementById('player-friend')?.addEventListener('click', () => {
    showToast('Друзья — скоро', 'info');
  });

  document.getElementById('player-pvp')?.addEventListener('click', async () => {
    try {
      await apiFetch('/api/pvp/duel', {
        method: 'POST',
        body: JSON.stringify({ opponent_username: profile!.username }),
      });
      showToast(`Вызов отправлен @${profile!.username}`, 'success');
    } catch (e) {
      const err = e as { message?: string };
      showToast(err.message ?? 'Ошибка', 'error');
    }
  });
}

// ═══════════════════════════════════════════
// УТИЛИТЫ
// ═══════════════════════════════════════════

function isBadgeType(value: string): value is BadgeType {
  return value === 'team' || value === 'plus' || value === 'trader' || value === 'admin' || value === 'verified';
}

function formatMoney(value: number): string {
  if (value >= 1_000_000) return (value / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (value >= 1_000) return (value / 1_000).toFixed(1).replace(/\.0$/, '') + 'k';
  return value.toLocaleString('ru-RU');
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function showToast(text: string, type: 'success' | 'error' | 'info'): void {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = text;
  document.body.appendChild(el);
  setTimeout(() => el.classList.add('visible'), 10);
  setTimeout(() => {
    el.classList.remove('visible');
    setTimeout(() => el.remove(), 300);
  }, 3000);
  } 

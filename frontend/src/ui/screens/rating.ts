/**
 * Рейтинг — топ по балансу, сезону, вечный.
 */

import { apiFetch } from '@/api/client';

interface TopUser {
  rank: number;
  username: string;
  balance: number;
  pvp_rating: number;
  pvp_wins_total: number;
  pvp_losses_total: number;
  collection_value: number;
}

interface RatingResponse {
  money: TopUser[];
  season: TopUser[];
  eternal: TopUser[];
}

const MEDALS = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'];

export async function renderRating(container: HTMLElement): Promise<void> {
  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.style.padding = '0 4px';
  title.innerHTML = `
    <iconify-icon icon="lucide:trophy" width="18" height="18"></iconify-icon>
    РЕЙТИНГ
  `;
  container.appendChild(title);

  const tabs = document.createElement('div');
  tabs.className = 'rating-tabs';
  tabs.innerHTML = `
    <button class="rating-tab active" data-tab="money">💰 Баланс</button>
    <button class="rating-tab" data-tab="season">⚔️ Сезон</button>
    <button class="rating-tab" data-tab="eternal">👑 Вечный</button>
  `;
  container.appendChild(tabs);

  const content = document.createElement('div');
  content.className = 'rating-content';
  container.appendChild(content);

  let data: RatingResponse | null = null;

  const render = (tab: string) => {
    if (!data) return;

    const users = data[tab as keyof RatingResponse] ?? [];

    if (users.length === 0) {
      content.innerHTML = '<div class="empty-state">Пусто</div>';
      return;
    }

    content.innerHTML = users
      .map((u, i) => {
        const medal = MEDALS[i] ?? `${i + 1}.`;

        let value = '';
        if (tab === 'money') {
          value = `💰 ${u.balance.toLocaleString('ru-RU')}`;
        } else if (tab === 'season') {
          value = `⚔️ ${u.pvp_rating} (${u.pvp_wins_total}W/${u.pvp_losses_total}L)`;
        } else {
          const total = u.pvp_wins_total + u.pvp_losses_total;
          const wr = total > 0 ? ((u.pvp_wins_total / total) * 100).toFixed(1) : '0.0';
          value = `👑 ${u.pvp_wins_total}W · WR ${wr}%`;
        }

        return `
          <div class="rating-item">
            <div class="rating-medal">${medal}</div>
            <div class="rating-info">
              <div class="rating-name">@${escapeHtml(u.username)}</div>
              <div class="rating-value">${value}</div>
            </div>
          </div>
        `;
      })
      .join('');
  };

  tabs.querySelectorAll('.rating-tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      tabs.querySelectorAll('.rating-tab').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const tab = (btn as HTMLElement).dataset.tab ?? 'money';
      render(tab);
    });
  });

  try {
    data = await apiFetch<RatingResponse>('/api/rating');
    render('money');
  } catch (e) {
    content.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
    console.error('[rating] failed', e);
  }
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

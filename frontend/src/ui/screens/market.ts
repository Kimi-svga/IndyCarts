/**
 * Биржа — покупка карт у бота.
 */

import { apiFetch } from '@/api/client';

interface MarketCard {
  id: number;
  name: string;
  rarity: string;
  team: string | null;
  year: number | null;
  price: number;
  base_price: number;
  image_url: string | null;
  max_supply: number | null;
  issued: number;
}

const RARITY_LABEL: Record<string, string> = {
  basic: 'BASIC',
  rare: 'RARE',
  epic: 'EPIC',
  mythic: 'MYTHIC',
  legendary: 'LEGENDARY',
  limited: 'LIMITED',
  season: 'SEASON',
};

export async function renderMarket(container: HTMLElement): Promise<void> {
  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.style.padding = '0 4px';
  title.innerHTML = `
    <iconify-icon icon="lucide:trending-up" width="18" height="18"></iconify-icon>
    БИРЖА
  `;
  container.appendChild(title);

  const grid = document.createElement('div');
  grid.className = 'cards-grid';
  grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;">Загрузка...</div>';
  container.appendChild(grid);

  const render = async () => {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;">Загрузка...</div>';

    let cards: MarketCard[] = [];
    try {
      cards = await apiFetch<MarketCard[]>('/api/market/list');
    } catch (e) {
      grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;">Ошибка загрузки</div>';
      return;
    }

    if (cards.length === 0) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1;">
          <iconify-icon icon="lucide:trending-up" width="48" height="48"></iconify-icon>
          <div class="empty-text">Биржа пуста</div>
        </div>
      `;
      return;
    }

    grid.innerHTML = cards
      .map((c) => {
        const hasLimit = c.max_supply !== null;
        const limitText = hasLimit ? `${c.issued}/${c.max_supply}` : '∞';

        return `
          <div class="card-item ${c.rarity}" data-card-id="${c.id}">
            <div class="card-image">
              <div class="card-number">#${c.id}</div>
              ${
                c.image_url
                  ? `<img src="${c.image_url}" alt="${escapeHtml(c.name)}" loading="lazy" />`
                  : '<iconify-icon icon="lucide:car" width="48" height="48"></iconify-icon>'
              }
              <div class="market-buy-badge">💰</div>
            </div>
            <div class="card-info">
              <div class="card-name">${escapeHtml(c.name)}</div>
              <div class="card-meta">
                <span>${RARITY_LABEL[c.rarity] ?? c.rarity}</span>
                <span class="card-price">${c.price.toLocaleString('ru-RU')}</span>
              </div>
              <div class="market-limit">Тираж: ${limitText}</div>
            </div>
          </div>
        `;
      })
      .join('');

    grid.querySelectorAll('[data-card-id]').forEach((el) => {
      el.addEventListener('click', async () => {
        const cardId = parseInt((el as HTMLElement).dataset.cardId ?? '0', 10);
        const card = cards.find((c) => c.id === cardId);
        if (!card) return;

        if (!confirm(`Купить "${card.name}" за ${card.price.toLocaleString('ru-RU')} монет?`)) {
          return;
        }

        try {
          const res = await apiFetch<{ ok: boolean; card_name: string; new_balance: number }>(
            '/api/market/buy',
            { method: 'POST', body: JSON.stringify({ card_id: cardId }) },
          );
          showToast(`✅ Куплено: ${res.card_name}`, 'success');
          await render();
        } catch (e) {
          const err = e as { message?: string };
          showToast(err.message ?? 'Ошибка', 'error');
        }
      });
    });
  };

  await render();
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

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
    } 

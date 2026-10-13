/**
 * Коллекция карт с кликом на карту.
 */

import { apiFetch } from '@/api/client';
import { openCardModal } from './card-detail';

interface CardItem {
  id: number;
  name: string;
  rarity: string;
  team: string | null;
  year: number | null;
  price: number;
  image_url: string | null;
  count: number;
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

export async function renderCollection(container: HTMLElement): Promise<void> {
  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.style.padding = '0 4px';
  title.innerHTML = `
    <iconify-icon icon="lucide:layers" width="18" height="18"></iconify-icon>
    КОЛЛЕКЦИЯ
  `;
  container.appendChild(title);

  const grid = document.createElement('div');
  grid.className = 'cards-grid';
  container.appendChild(grid);

  const render = async () => {
    grid.innerHTML = '';

    let cards: CardItem[] = [];
    try {
      cards = await apiFetch<CardItem[]>('/api/cards');
    } catch (e) {
      console.error('[collection] failed to load', e);
    }

    if (cards.length === 0) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <iconify-icon icon="lucide:package-open" width="48" height="48"></iconify-icon>
          <div class="empty-text">Коллекция пуста</div>
          <div class="empty-sub">Сделай первый дроп</div>
        </div>
      `;
      return;
    }

    for (const card of cards) {
      const el = document.createElement('div');
      el.className = `card-item ${card.rarity}`;
      el.innerHTML = `
        <div class="card-image">
          <div class="card-number">#${card.id}</div>
          ${
            card.image_url
              ? `<img src="${card.image_url}" alt="${escapeHtml(card.name)}" loading="lazy" />`
              : '<iconify-icon icon="lucide:car" width="48" height="48"></iconify-icon>'
          }
          ${
            card.count > 1
              ? `<div class="card-count">×${card.count}</div>`
              : ''
          }
        </div>
        <div class="card-info">
          <div class="card-name">${escapeHtml(card.name)}</div>
          <div class="card-meta">
            <span>${RARITY_LABEL[card.rarity] ?? card.rarity}</span>
            <span class="card-price">${card.price.toLocaleString('ru-RU')}</span>
          </div>
        </div>
      `;

      el.addEventListener('click', () => {
        openCardModal(card, () => {
          void render();
        });
      });

      grid.appendChild(el);
    }
  };

  await render();
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

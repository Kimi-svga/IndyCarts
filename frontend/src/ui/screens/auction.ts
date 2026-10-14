/**
 * Аукцион — лоты, ставки, выкуп.
 */

import { apiFetch } from '@/api/client';
import { Modal } from '../components/modal';

interface AuctionLot {
  id: number;
  seller: string;
  card_id: number;
  card_name: string;
  rarity: string;
  image_url: string | null;
  start_price: number;
  buyout_price: number | null;
  current_bid: number;
  current_bidder: string | null;
  bid_count: number;
  ends_at: string;
  ends_in_minutes: number;
}

export async function renderAuction(container: HTMLElement): Promise<void> {
  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.style.padding = '0 4px';
  title.innerHTML = `
    <iconify-icon icon="lucide:target" width="18" height="18"></iconify-icon>
    АУКЦИОН
  `;
  container.appendChild(title);

  const list = document.createElement('div');
  list.className = 'auction-list';
  list.innerHTML = '<div class="empty-state">Загрузка...</div>';
  container.appendChild(list);

  const render = async () => {
    list.innerHTML = '<div class="empty-state">Загрузка...</div>';

    let lots: AuctionLot[] = [];
    try {
      lots = await apiFetch<AuctionLot[]>('/api/auction/list');
    } catch (e) {
      list.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
      return;
    }

    if (lots.length === 0) {
      list.innerHTML = `
        <div class="empty-state">
          <iconify-icon icon="lucide:target" width="48" height="48"></iconify-icon>
          <div class="empty-text">Активных лотов нет</div>
          <div class="empty-sub">Скоро появятся</div>
        </div>
      `;
      return;
    }

    list.innerHTML = lots
      .map((lot) => {
        const timeStr = formatTime(lot.ends_in_minutes);
        const price = lot.current_bid || lot.start_price;

        return `
          <div class="auction-item" data-lot-id="${lot.id}">
            <div class="auction-image">
              ${
                lot.image_url
                  ? `<img src="${lot.image_url}" alt="${escapeHtml(lot.card_name)}" loading="lazy" />`
                  : '<iconify-icon icon="lucide:car" width="40" height="40"></iconify-icon>'
              }
            </div>
            <div class="auction-info">
              <div class="auction-name">${escapeHtml(lot.card_name)}</div>
              <div class="auction-meta">@${escapeHtml(lot.seller)} · ${lot.bid_count} ставок</div>
              <div class="auction-price">
                💰 ${price.toLocaleString('ru-RU')}
                ${lot.current_bidder ? `<span class="auction-bidder">@${escapeHtml(lot.current_bidder)}</span>` : ''}
              </div>
              <div class="auction-time">⏰ ${timeStr}</div>
            </div>
            <div class="auction-actions">
              <button class="auction-mini-btn primary" data-bid="${lot.id}">💰</button>
              ${lot.buyout_price ? `<button class="auction-mini-btn default" data-buyout="${lot.id}">⚡</button>` : ''}
            </div>
          </div>
        `;
      })
      .join('');

    list.querySelectorAll('[data-bid]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = parseInt((btn as HTMLElement).dataset.bid ?? '0', 10);
        const lot = lots.find((l) => l.id === id);
        if (lot) openBidModal(lot, render);
      });
    });

    list.querySelectorAll('[data-buyout]').forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = parseInt((btn as HTMLElement).dataset.buyout ?? '0', 10);
        const lot = lots.find((l) => l.id === id);
        if (!lot || !lot.buyout_price) return;

        if (!confirm(`Выкупить "${lot.card_name}" за ${lot.buyout_price.toLocaleString('ru-RU')}?`)) {
          return;
        }

        try {
          await apiFetch('/api/auction/buyout', {
            method: 'POST',
            body: JSON.stringify({ lot_id: id }),
          });
          showToast('⚡ Куплено!', 'success');
          await render();
        } catch (err) {
          const e2 = err as { message?: string };
          showToast(e2.message ?? 'Ошибка', 'error');
        }
      });
    });
  };

  await render();
}

function openBidModal(lot: AuctionLot, onUpdate: () => void): void {
  const modal = new Modal();
  const minBid = Math.max(lot.current_bid + 1, lot.start_price);

  modal.show(`
    <div class="modal-title">💰 Ставка</div>
    <div class="modal-subtitle">${escapeHtml(lot.card_name)}</div>
    <div class="info-row"><span class="info-row-label">Текущая</span><span class="info-row-value">${(lot.current_bid || lot.start_price).toLocaleString('ru-RU')}</span></div>
    <div class="info-row"><span class="info-row-label">Минимум</span><span class="info-row-value gold">${minBid.toLocaleString('ru-RU')}</span></div>
    <input type="number" id="bid-amount" class="modal-input" placeholder="${minBid}" />
    <div class="modal-actions">
      <button class="modal-action primary" id="bid-confirm">Поставить</button>
      <button class="modal-action default" id="bid-cancel">Отмена</button>
    </div>
  `);

  const input = document.getElementById('bid-amount') as HTMLInputElement | null;
  input?.focus();

  document.getElementById('bid-cancel')?.addEventListener('click', () => modal.close());
  document.getElementById('bid-confirm')?.addEventListener('click', async () => {
    const amount = parseInt(input?.value ?? '0', 10);
    if (!amount || amount < minBid) {
      showToast(`Минимум ${minBid.toLocaleString('ru-RU')}`, 'error');
      return;
    }

    try {
      await apiFetch('/api/auction/bid', {
        method: 'POST',
        body: JSON.stringify({ lot_id: lot.id, amount }),
      });
      modal.close();
      showToast(`✅ Ставка ${amount.toLocaleString('ru-RU')}`, 'success');
      onUpdate();
    } catch (e) {
      const err = e as { message?: string };
      showToast(err.message ?? 'Ошибка', 'error');
    }
  });
}

function formatTime(minutes: number): string {
  if (minutes <= 0) return 'истёк';
  if (minutes < 60) return `${minutes}м`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h < 24) return `${h}ч ${m}м`;
  return `${Math.floor(h / 24)}д ${h % 24}ч`;
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
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Магазин — попытки, Indy+.
 */

import { apiFetch } from '@/api/client';

interface ShopInfo {
  coin_per_attempt: number;
  max_attempts_per_day: number;
  shop_attempts_today: number;
  balance: number;
  plus_price_coins: number;
  plus_price_stars: number;
  plus_duration_days: number;
}

export async function renderShop(container: HTMLElement): Promise<void> {
  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.style.padding = '0 4px';
  title.innerHTML = `
    <iconify-icon icon="lucide:shopping-cart" width="18" height="18"></iconify-icon>
    МАГАЗИН
  `;
  container.appendChild(title);

  const content = document.createElement('div');
  container.appendChild(content);

  const render = async () => {
    content.innerHTML = '<div class="empty-state">Загрузка...</div>';

    let info: ShopInfo | null = null;
    try {
      info = await apiFetch<ShopInfo>('/api/shop/info');
    } catch (e) {
      content.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
      return;
    }

    if (!info) return;

    const attemptsLeft = info.max_attempts_per_day - info.shop_attempts_today;

    content.innerHTML = `
      <div class="info-card">
        <div class="info-card-title">
          <iconify-icon icon="lucide:gift" width="18" height="18"></iconify-icon>
          ПОПЫТКИ
        </div>
        <div class="info-row"><span class="info-row-label">Курс</span><span class="info-row-value">${info.coin_per_attempt} монет / попытка</span></div>
        <div class="info-row"><span class="info-row-label">Куплено сегодня</span><span class="info-row-value">${info.shop_attempts_today} / ${info.max_attempts_per_day}</span></div>
        <div class="info-row"><span class="info-row-label">Баланс</span><span class="info-row-value gold">${info.balance.toLocaleString('ru-RU')}</span></div>
        <div class="shop-actions">
          <button class="shop-btn" data-amount="2">🎴 2 попытки</button>
          <button class="shop-btn" data-amount="5">🎴 5 попыток</button>
          <button class="shop-btn" data-amount="10">🎴 10 попыток</button>
        </div>
      </div>

      <div class="info-card">
        <div class="info-card-title">
          <iconify-icon icon="lucide:gem" width="18" height="18"></iconify-icon>
          INDY+
        </div>
        <div class="info-row"><span class="info-row-label">Цена</span><span class="info-row-value">${info.plus_price_stars} ⭐ / ${info.plus_price_coins.toLocaleString('ru-RU')} монет</span></div>
        <div class="info-row"><span class="info-row-label">Срок</span><span class="info-row-value">${info.plus_duration_days} дней</span></div>
        <div class="shop-plus-info">
          +5 попыток в день · ×1.2 PvP · 7% роялти · 5% аукцион
        </div>
        <div class="shop-actions">
          <button class="shop-btn primary" id="shop-plus">
            ⭐ ОТКРЫТЬ В БОТЕ
          </button>
        </div>
      </div>

      <div class="shop-attempts-left">
        Осталось купить сегодня: <b>${Math.max(0, attemptsLeft)}</b>
      </div>
    `;

    content.querySelectorAll('[data-amount]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const amount = parseInt((btn as HTMLElement).dataset.amount ?? '0', 10);
        if (!amount) return;

        try {
          const res = await apiFetch<{ ok: boolean; attempts: number; cost: number; total_attempts: number }>(
            '/api/shop/attempts',
            { method: 'POST', body: JSON.stringify({ attempts: amount }) },
          );
          showToast(`✅ +${res.attempts} попыток за ${res.cost} монет`, 'success');
          await render();
        } catch (e) {
          const err = e as { message?: string };
          showToast(err.message ?? 'Ошибка', 'error');
        }
      });
    });

    document.getElementById('shop-plus')?.addEventListener('click', () => {
      showToast('Открой бота → /plus', 'info');
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

/**
 * Дроп карт с анимацией.
 */

import { apiFetch } from '@/api/client';

interface DropResult {
  ok: boolean;
  card: {
    id: number;
    name: string;
    rarity: string;
    team: string | null;
    year: number | null;
    price: number;
    image_url: string | null;
    max_supply: number | null;
    issued: number;
  };
  is_iw: boolean;
  serial: number | null;
  bonus_money: number;
  attempts_left: number;
  new_balance: number;
}

interface MeData {
  daily_attempts: number;
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

export async function renderDrop(container: HTMLElement): Promise<void> {
  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.style.padding = '0 4px';
  title.innerHTML = `
    <iconify-icon icon="lucide:gift" width="18" height="18"></iconify-icon>
    ДРОП КАРТ
  `;
  container.appendChild(title);

  const stage = document.createElement('div');
  stage.className = 'drop-stage';
  stage.innerHTML = `
    <div class="drop-placeholder" id="drop-placeholder">
      <iconify-icon icon="lucide:gift" width="80" height="80"></iconify-icon>
    </div>
    <div class="drop-result" id="drop-result"></div>
  `;
  container.appendChild(stage);

  const btn = document.createElement('button');
  btn.className = 'drop-btn';
  btn.id = 'drop-btn';
  btn.innerHTML = `
    <iconify-icon icon="lucide:gift" width="18" height="18"></iconify-icon>
    <span id="drop-btn-label">ЗАГРУЗКА...</span>
  `;
  container.appendChild(btn);

  const counter = document.createElement('div');
  counter.className = 'drop-counter';
  counter.id = 'drop-counter';
  container.appendChild(counter);

  const updateCounter = async () => {
    try {
      const me = await apiFetch<MeData>('/api/me');
      const label = document.getElementById('drop-btn-label');
      const counterEl = document.getElementById('drop-counter');
      const btnEl = document.getElementById('drop-btn') as HTMLButtonElement | null;

      if (label) {
        label.textContent = me.daily_attempts > 0 ? 'ДРОПНУТЬ' : 'НЕТ ПОПЫТОК';
      }
      if (counterEl) {
        counterEl.innerHTML = `Осталось сегодня: <b>${me.daily_attempts}</b> попыток`;
      }
      if (btnEl) {
        btnEl.disabled = me.daily_attempts <= 0;
      }
    } catch (e) {
      console.error('[drop] failed to load me', e);
    }
  };

  await updateCounter();

  btn.addEventListener('click', async () => {
    const btnEl = btn as HTMLButtonElement;
    if (btnEl.disabled) return;

    btnEl.disabled = true;

    const placeholder = document.getElementById('drop-placeholder');
    const resultEl = document.getElementById('drop-result');
    const label = document.getElementById('drop-btn-label');

    if (label) label.textContent = 'ДРОП...';
    if (resultEl) resultEl.classList.remove('visible');

    const icons = ['lucide:gift', 'lucide:car', 'lucide:flag', 'lucide:star', 'lucide:trophy'];
    let ticks = 0;
    const interval = window.setInterval(() => {
      if (placeholder) {
        placeholder.innerHTML = `<iconify-icon icon="${icons[ticks % icons.length]}" width="80" height="80"></iconify-icon>`;
      }
      ticks++;
    }, 80);

    let data: DropResult | null = null;
    let errorMsg: string | null = null;

    try {
      data = await apiFetch<DropResult>('/api/drop', { method: 'POST' });
    } catch (e) {
      const err = e as { message?: string };
      errorMsg = err.message ?? 'Ошибка дропа';
    }

    await new Promise((r) => setTimeout(r, 1200));

    window.clearInterval(interval);

    if (placeholder) {
      placeholder.innerHTML = '<iconify-icon icon="lucide:gift" width="80" height="80"></iconify-icon>';
    }

    if (errorMsg || !data) {
      showToast(errorMsg ?? 'Ошибка', 'error');
      btnEl.disabled = false;
      if (label) label.textContent = 'ДРОПНУТЬ';
      await updateCounter();
      return;
    }

    const card = data.card;
    const rarityLabel = RARITY_LABEL[card.rarity] ?? card.rarity;
    const iwText = data.is_iw ? '<div class="drop-iw">⭐ INDY WINNER!</div>' : '';
    const serialText = data.serial
      ? `<div class="drop-serial">№ ${data.serial}${card.max_supply ? ` / ${card.max_supply}` : ''}</div>`
      : '';
    const bonusText = data.bonus_money > 0
      ? `<div class="drop-bonus">💰 +${data.bonus_money} монет</div>`
      : '';

    if (resultEl) {
      resultEl.innerHTML = `
        <div class="drop-card ${card.rarity}">
          <div class="drop-card-number">#${card.id}</div>
          ${
            card.image_url
              ? `<img src="${card.image_url}" alt="${escapeHtml(card.name)}" />`
              : '<iconify-icon icon="lucide:car" width="96" height="96"></iconify-icon>'
          }
        </div>
        <div class="drop-card-name">${escapeHtml(card.name)}</div>
        <div class="drop-card-rarity ${card.rarity}">${rarityLabel}</div>
        ${iwText}
        ${serialText}
        <div class="drop-card-price">💰 ${card.price.toLocaleString('ru-RU')}</div>
        ${bonusText}
      `;
      resultEl.classList.add('visible');
    }

    const messages: Record<string, string> = {
      legendary: '🔥 ЛЕГЕНДАРНАЯ КАРТА!',
      mythic: '⭐ МИФИЧЕСКАЯ КАРТА!',
      epic: '🟣 ЭПИЧЕСКАЯ КАРТА!',
      rare: '🟢 РЕДКАЯ КАРТА!',
      limited: '🔴 LIMITED!',
      season: '⭐ SEASON!',
      basic: '🔵 Обычная карта',
    };

    const toastType = data.is_iw ? 'success' : 'info';
    showToast(messages[card.rarity] ?? 'Карта получена', toastType);

    await updateCounter();
  });
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

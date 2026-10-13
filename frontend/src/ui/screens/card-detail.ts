/**
 * Модалка карты + действия.
 */

import { Modal } from '../components/modal';
import { apiFetch } from '@/api/client';

interface CardData {
  id: number;
  name: string;
  rarity: string;
  team: string | null;
  year: number | null;
  price: number;
  image_url: string | null;
  count: number;
}

export function openCardModal(
  card: CardData,
  onUpdate: () => void,
): void {
  const modal = new Modal();

  modal.showCard(card, [
    {
      label: 'Инфо',
      icon: 'lucide:info',
      onClick: () => {
        showToast(
          `${card.name}\n${card.rarity}\n${card.team ?? '—'} · ${card.year ?? '—'}\n💰 ${card.price.toLocaleString('ru-RU')}\n×${card.count}`,
          'info',
        );
      },
    },
    {
      label: 'Продать за 90%',
      icon: 'lucide:coins',
      variant: 'primary',
      onClick: async () => {
        try {
          await apiFetch('/api/card/sell', {
            method: 'POST',
            body: JSON.stringify({ card_id: card.id }),
          });
          modal.close();
          onUpdate();
          showToast('Карта продана!', 'success');
        } catch (e) {
          const err = e as { message?: string };
          showToast(err.message ?? 'Ошибка продажи', 'error');
        }
      },
    },
    {
      label: 'Подарить',
      icon: 'lucide:gift',
      onClick: () => {
        modal.close();
        openGiftModal(card, onUpdate);
      },
    },
    {
      label: 'Закрыть',
      icon: 'lucide:x',
      onClick: () => {
        modal.close();
      },
    },
  ]);
}

function openGiftModal(card: CardData, onUpdate: () => void): void {
  const modal = new Modal();

  modal.show(`
    <div class="modal-title">🎁 Подарить карту</div>
    <div class="modal-subtitle">${card.name}</div>
    <input
      type="text"
      id="gift-username"
      class="modal-input"
      placeholder="@username"
      autocorrect="off"
      autocapitalize="off"
      spellcheck="false"
    />
    <div class="modal-actions">
      <button class="modal-action primary" id="gift-send">
        <iconify-icon icon="lucide:send" width="16" height="16"></iconify-icon>
        <span>Отправить</span>
      </button>
      <button class="modal-action default" id="gift-cancel">
        <iconify-icon icon="lucide:x" width="16" height="16"></iconify-icon>
        <span>Отмена</span>
      </button>
    </div>
  `);

  const input = document.getElementById('gift-username') as HTMLInputElement | null;
  const sendBtn = document.getElementById('gift-send');
  const cancelBtn = document.getElementById('gift-cancel');

  input?.focus();

  cancelBtn?.addEventListener('click', () => modal.close());

  sendBtn?.addEventListener('click', async () => {
    const username = input?.value.trim().replace('@', '') ?? '';
    if (username.length < 3) {
      showToast('Введи @username', 'error');
      return;
    }

    try {
      await apiFetch('/api/card/gift', {
        method: 'POST',
        body: JSON.stringify({ card_id: card.id, username }),
      });
      modal.close();
      onUpdate();
      showToast(`Карта подарена @${username}`, 'success');
    } catch (e) {
      const err = e as { message?: string };
      showToast(err.message ?? 'Ошибка подарка', 'error');
    }
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

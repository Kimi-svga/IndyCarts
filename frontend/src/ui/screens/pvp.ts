/**
 * PvP — вызовы, бои, ставки.
 */

import { apiFetch } from '@/api/client';
import { Modal } from '../components/modal';

interface BattleItem {
  id: number;
  challenger: string;
  opponent: string | null;
  opponent_username: string;
  direction: 'incoming' | 'outgoing';
  money_stake: number;
  created_at: string;
}

interface BattlesResponse {
  incoming: BattleItem[];
  outgoing: BattleItem[];
}

interface BattleCard {
  user_card_id: number;
  card_id: number;
  name: string;
  rarity: string;
  price: number;
  image_url: string | null;
  is_chosen: boolean;
}

interface BattleDetail {
  id: number;
  status: string;
  challenger: string;
  opponent: string | null;
  challenger_ready: boolean;
  opponent_ready: boolean;
  money_stake: number;
  my_cards: BattleCard[];
  chosen_count: number;
  max_stakes: number;
}

export async function renderPvp(container: HTMLElement): Promise<void> {
  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.style.padding = '0 4px';
  title.innerHTML = `
    <iconify-icon icon="lucide:swords" width="18" height="18"></iconify-icon>
    PVP
  `;
  container.appendChild(title);

  const actions = document.createElement('div');
  actions.className = 'pvp-actions';
  actions.innerHTML = `
    <button class="pvp-btn primary" id="pvp-find">
      <iconify-icon icon="lucide:swords" width="18" height="18"></iconify-icon>
      НАЙТИ ПРОТИВНИКА
    </button>
    <button class="pvp-btn default" id="pvp-duel">
      <iconify-icon icon="lucide:user-plus" width="18" height="18"></iconify-icon>
      ВЫЗВАТЬ ПО НИКУ
    </button>
  `;
  container.appendChild(actions);

  const list = document.createElement('div');
  list.className = 'pvp-list';
  container.appendChild(list);

  const render = async () => {
    list.innerHTML = '<div class="pvp-empty">Загрузка...</div>';

    try {
      const data = await apiFetch<BattlesResponse>('/api/pvp/battles');
      const all = [...data.incoming, ...data.outgoing];

      if (all.length === 0) {
        list.innerHTML = `
          <div class="pvp-empty">
            <iconify-icon icon="lucide:swords" width="48" height="48"></iconify-icon>
            <div>Активных боёв нет</div>
            <div style="font-size:12px; opacity:0.6;">Найди противника или вызови по нику</div>
          </div>
        `;
        return;
      }

      list.innerHTML = all
        .map((b) => {
          const isIncoming = b.direction === 'incoming';
          return `
            <div class="pvp-battle ${isIncoming ? 'incoming' : 'outgoing'}">
              <div class="pvp-battle-info">
                <div class="pvp-battle-title">
                  ${isIncoming ? '⚔️ Вызов от' : '📤 Вызов к'} <b>@${b.opponent_username}</b>
                </div>
                <div class="pvp-battle-meta">💰 ${b.money_stake} монет</div>
              </div>
              <div class="pvp-battle-actions">
                ${
                  isIncoming
                    ? `
                      <button class="pvp-mini-btn primary" data-action="accept" data-id="${b.id}">⚔️</button>
                      <button class="pvp-mini-btn danger" data-action="decline" data-id="${b.id}">❌</button>
                    `
                    : `
                      <button class="pvp-mini-btn default" data-action="open" data-id="${b.id}">🎴</button>
                      <button class="pvp-mini-btn danger" data-action="decline" data-id="${b.id}">❌</button>
                    `
                }
              </div>
            </div>
          `;
        })
        .join('');

      list.querySelectorAll('[data-action]').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const action = (btn as HTMLElement).dataset.action;
          const id = parseInt((btn as HTMLElement).dataset.id ?? '0', 10);

          if (action === 'accept' || action === 'open') {
            await openBattleModal(id, render);
          } else if (action === 'decline') {
            try {
              await apiFetch('/api/pvp/decline', {
                method: 'POST',
                body: JSON.stringify({ battle_id: id }),
              });
              showToast('Вызов отклонён', 'info');
              await render();
            } catch (e) {
              const err = e as { message?: string };
              showToast(err.message ?? 'Ошибка', 'error');
            }
          }
        });
      });
    } catch (e) {
      list.innerHTML = '<div class="pvp-empty">Ошибка загрузки</div>';
      console.error('[pvp] failed', e);
    }
  };

  await render();

  document.getElementById('pvp-find')?.addEventListener('click', async () => {
    try {
      const res = await apiFetch<{ ok: boolean; battle_id: number; opponent: string }>(
        '/api/pvp/find',
        { method: 'POST' },
      );
      showToast(`Вызов @${res.opponent}`, 'success');
      await render();
    } catch (e) {
      const err = e as { message?: string };
      showToast(err.message ?? 'Ошибка', 'error');
    }
  });

  document.getElementById('pvp-duel')?.addEventListener('click', () => {
    openDuelModal(render);
  });
}

function openDuelModal(onUpdate: () => void): void {
  const modal = new Modal();

  modal.show(`
    <div class="modal-title">⚔️ Вызвать игрока</div>
    <div class="modal-subtitle">Введи @username</div>
    <input type="text" id="duel-username" class="modal-input" placeholder="@username"
      autocorrect="off" autocapitalize="off" spellcheck="false" />
    <div class="modal-actions">
      <button class="modal-action primary" id="duel-send">Вызвать</button>
      <button class="modal-action default" id="duel-cancel">Отмена</button>
    </div>
  `);

  const input = document.getElementById('duel-username') as HTMLInputElement | null;
  input?.focus();

  document.getElementById('duel-cancel')?.addEventListener('click', () => modal.close());
  document.getElementById('duel-send')?.addEventListener('click', async () => {
    const username = input?.value.trim().replace('@', '') ?? '';
    if (username.length < 3) {
      showToast('Введи @username', 'error');
      return;
    }

    try {
      const res = await apiFetch<{ ok: boolean; opponent: string }>(
        '/api/pvp/duel',
        { method: 'POST', body: JSON.stringify({ opponent_username: username }) },
      );
      modal.close();
      showToast(`Вызов @${res.opponent}`, 'success');
      onUpdate();
    } catch (e) {
      const err = e as { message?: string };
      showToast(err.message ?? 'Ошибка', 'error');
    }
  });
}

async function openBattleModal(battleId: number, onUpdate: () => void): Promise<void> {
  const modal = new Modal();

  const render = async () => {
    try {
      const battle = await apiFetch<BattleDetail>(`/api/pvp/battle/${battleId}`);

      const cardsHtml = battle.my_cards
        .map(
          (c) => `
            <div class="pvp-card ${c.is_chosen ? 'chosen' : ''} ${c.rarity}" data-uc="${c.user_card_id}">
              <div class="pvp-card-img">
                ${
                  c.image_url
                    ? `<img src="${c.image_url}" alt="${escapeHtml(c.name)}" loading="lazy" />`
                    : '<iconify-icon icon="lucide:car" width="40" height="40"></iconify-icon>'
                }
                ${c.is_chosen ? '<div class="pvp-card-check">✓</div>' : ''}
              </div>
              <div class="pvp-card-name">${escapeHtml(c.name)}</div>
              <div class="pvp-card-price">${c.price.toLocaleString('ru-RU')}</div>
            </div>
          `,
        )
        .join('');

      modal.show(`
        <div class="modal-title">⚔️ Бой #${battle.id}</div>
        <div class="modal-subtitle">${battle.challenger} vs ${battle.opponent ?? '?'}</div>
        <div class="pvp-status">Выбрано карт: <b>${battle.chosen_count} / ${battle.max_stakes}</b></div>
        <div class="pvp-cards-grid">${cardsHtml}</div>
        <div class="modal-actions">
          <button class="modal-action primary" id="pvp-ready">ГОТОВ</button>
          <button class="modal-action default" id="pvp-close">Закрыть</button>
        </div>
      `);

      const content = modal['contentEl'] as HTMLElement;
      content.querySelectorAll('.pvp-card').forEach((el) => {
        el.addEventListener('click', async () => {
          const ucId = parseInt((el as HTMLElement).dataset.uc ?? '0', 10);
          try {
            await apiFetch('/api/pvp/stake', {
              method: 'POST',
              body: JSON.stringify({ battle_id: battleId, user_card_ids: [ucId] }),
            });
            await render();
          } catch (e) {
            const err = e as { message?: string };
            showToast(err.message ?? 'Ошибка', 'error');
          }
        });
      });

      document.getElementById('pvp-ready')?.addEventListener('click', async () => {
        try {
          const res = await apiFetch<{ ok: boolean; both_ready: boolean }>(
            '/api/pvp/ready',
            { method: 'POST', body: JSON.stringify({ battle_id: battleId }) },
          );

          if (res.both_ready) {
            modal.close();
            showToast('⚔️ Бой завершён!', 'success');
            onUpdate();
          } else {
            showToast('✅ Ждём противника...', 'info');
          }
        } catch (e) {
          const err = e as { message?: string };
          showToast(err.message ?? 'Ошибка', 'error');
        }
      });

      document.getElementById('pvp-close')?.addEventListener('click', () => modal.close());
    } catch (e) {
      const err = e as { message?: string };
      showToast(err.message ?? 'Ошибка', 'error');
    }
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

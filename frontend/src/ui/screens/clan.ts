/**
 * Кланы — список, создать, вступить.
 */

import { apiFetch } from '@/api/client';
import { Modal } from '../components/modal';

interface ClanInfo {
  id: number;
  name: string;
  tag: string;
  level: number;
  xp: number;
  treasury: number;
  members_count: number;
  is_open: boolean;
  owner: string;
}

interface MyClan {
  clan: ClanInfo | null;
  role: string | null;
}

export async function renderClan(container: HTMLElement): Promise<void> {
  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.style.padding = '0 4px';
  title.innerHTML = `
    <iconify-icon icon="lucide:shield" width="18" height="18"></iconify-icon>
    КЛАНЫ
  `;
  container.appendChild(title);

  const content = document.createElement('div');
  container.appendChild(content);

  const render = async () => {
    content.innerHTML = '<div class="empty-state">Загрузка...</div>';

    let my: MyClan | null = null;
    let allClans: ClanInfo[] = [];

    try {
      my = await apiFetch<MyClan>('/api/clan/my');
      allClans = await apiFetch<ClanInfo[]>('/api/clan/list');
    } catch (e) {
      content.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
      return;
    }

    if (my?.clan) {
      const c = my.clan;
      const bonuses = getLevelBonuses(c.level);

      content.innerHTML = `
        <div class="clan-hero">
          <div class="clan-tag-name">[${c.tag}] ${c.name}</div>
          <div class="clan-meta">Уровень ${c.level} · ${c.members_count} участников</div>
          <div class="clan-stats">
            <div class="clan-stat">
              <div class="clan-stat-value">${c.xp.toLocaleString('ru-RU')}</div>
              <div class="clan-stat-label">XP</div>
            </div>
            <div class="clan-stat">
              <div class="clan-stat-value">${c.treasury.toLocaleString('ru-RU')}</div>
              <div class="clan-stat-label">Казна</div>
            </div>
            <div class="clan-stat">
              <div class="clan-stat-value">${c.members_count}</div>
              <div class="clan-stat-label">Людей</div>
            </div>
          </div>
          <div class="clan-role">Твоя роль: ${roleLabel(my.role)}</div>
        </div>

        <div class="info-card">
          <div class="info-card-title">Бонусы клана</div>
          <div class="info-row"><span class="info-row-label">🍀 Дроп</span><span class="info-row-value green">+${(bonuses.drop * 100).toFixed(0)}%</span></div>
          <div class="info-row"><span class="info-row-label">💰 Монеты</span><span class="info-row-value green">+${(bonuses.money * 100).toFixed(0)}%</span></div>
          <div class="info-row"><span class="info-row-label">🎯 Аукцион</span><span class="info-row-value blue">−${bonuses.auction.toFixed(1)}%</span></div>
          <div class="info-row"><span class="info-row-label">🎴 Попытки</span><span class="info-row-value">+${bonuses.attempts}</span></div>
        </div>
      `;
      return;
    }

    content.innerHTML = `
      <div class="clan-actions">
        <button class="clan-btn primary" id="clan-create">
          <iconify-icon icon="lucide:plus" width="18" height="18"></iconify-icon>
          СОЗДАТЬ КЛАН
        </button>
      </div>
      <div class="info-card-title" style="padding: 0 4px; margin-top: 16px;">Все кланы</div>
      <div class="clan-list">
        ${
          allClans.length === 0
            ? '<div class="empty-state">Кланов нет</div>'
            : allClans
                .map(
                  (c) => `
                    <div class="clan-item" data-clan-id="${c.id}">
                      <div class="clan-item-tag">[${c.tag}]</div>
                      <div class="clan-item-info">
                        <div class="clan-item-name">${escapeHtml(c.name)}</div>
                        <div class="clan-item-meta">ур.${c.level} · ${c.members_count} 👥 ${c.is_open ? '🔓' : '🔒'}</div>
                      </div>
                      ${
                        c.is_open
                          ? `<button class="clan-mini-btn primary" data-join="${c.id}">Вступить</button>`
                          : '<span class="clan-lock">🔒</span>'
                      }
                    </div>
                  `,
                )
                .join('')
        }
      </div>
    `;

    document.getElementById('clan-create')?.addEventListener('click', () => {
      openCreateClanModal(render);
    });

    content.querySelectorAll('[data-join]').forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = parseInt((btn as HTMLElement).dataset.join ?? '0', 10);
        try {
          await apiFetch('/api/clan/join', {
            method: 'POST',
            body: JSON.stringify({ clan_id: id }),
          });
          showToast('✅ Вступил в клан!', 'success');
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

function openCreateClanModal(onUpdate: () => void): void {
  const modal = new Modal();

  modal.show(`
    <div class="modal-title">🏰 Создать клан</div>
    <div class="modal-subtitle">Стоимость: 200,000 монет</div>
    <input type="text" id="clan-name" class="modal-input" placeholder="Название (3-24)" autocorrect="off" />
    <input type="text" id="clan-tag" class="modal-input" placeholder="Тег (2-4 буквы)" autocorrect="off" />
    <div class="modal-actions">
      <button class="modal-action primary" id="clan-confirm">Создать</button>
      <button class="modal-action default" id="clan-cancel">Отмена</button>
    </div>
  `);

  document.getElementById('clan-cancel')?.addEventListener('click', () => modal.close());

  document.getElementById('clan-confirm')?.addEventListener('click', async () => {
    const name = (document.getElementById('clan-name') as HTMLInputElement)?.value.trim();
    const tag = (document.getElementById('clan-tag') as HTMLInputElement)?.value.trim().toUpperCase();

    if (!name || name.length < 3 || name.length > 24) {
      showToast('Название: 3-24', 'error');
      return;
    }
    if (!tag || tag.length < 2 || tag.length > 4) {
      showToast('Тег: 2-4 буквы', 'error');
      return;
    }

    try {
      await apiFetch('/api/clan/create', {
        method: 'POST',
        body: JSON.stringify({ name, tag }),
      });
      modal.close();
      showToast('✅ Клан создан!', 'success');
      onUpdate();
    } catch (e) {
      const err = e as { message?: string };
      showToast(err.message ?? 'Ошибка', 'error');
    }
  });
}

function getLevelBonuses(level: number): { drop: number; money: number; auction: number; attempts: number } {
  const table: Record<number, { drop: number; money: number; auction: number; attempts: number }> = {
    1: { drop: 0, money: 0, auction: 0, attempts: 0 },
    2: { drop: 0.05, money: 0.05, auction: 0.5, attempts: 0 },
    3: { drop: 0.1, money: 0.1, auction: 1, attempts: 0 },
    4: { drop: 0.15, money: 0.15, auction: 1.5, attempts: 1 },
    5: { drop: 0.2, money: 0.2, auction: 2, attempts: 1 },
    6: { drop: 0.25, money: 0.25, auction: 2.5, attempts: 2 },
    7: { drop: 0.3, money: 0.3, auction: 3, attempts: 2 },
    8: { drop: 0.35, money: 0.35, auction: 3.5, attempts: 3 },
    9: { drop: 0.4, money: 0.4, auction: 4, attempts: 3 },
    10: { drop: 0.5, money: 0.5, auction: 5, attempts: 5 },
  };
  return table[level] ?? table[1];
}

function roleLabel(role: string | null): string {
  const map: Record<string, string> = {
    leader: '👑 Лидер',
    officer: '⚔️ Офицер',
    member: '👤 Участник',
  };
  return map[role ?? 'member'] ?? '👤 Участник';
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

/**
 * Профиль игрока.
 */

interface MeData {
  telegram_id: number;
  username: string;
  balance: number;
  cards_count: number;
  collection_value: number;
  pvp_rating: number;
  pvp_wins: number;
  pvp_losses: number;
  daily_streak: number;
  trust_score: number;
  daily_attempts: number;
  plus_tier: string;
  plus_expires_at: string | null;
  ban_level: string;
}

export function renderProfile(
  container: HTMLElement,
  userData: MeData | null,
): void {
  if (!userData) {
    container.innerHTML = `
      <div class="empty-state">
        <iconify-icon icon="lucide:user-x" width="48" height="48"></iconify-icon>
        <div class="empty-text">Не авторизован</div>
        <div class="empty-sub">Открой приложение через Telegram</div>
      </div>
    `;
    return;
  }

  const d = userData;

  const rows: Array<[string, string, string?]> = [
    ['Ник', `@${d.username}`, 'green'],
    ['Telegram ID', String(d.telegram_id)],
    ['Баланс', d.balance.toLocaleString('ru-RU'), 'gold'],
    ['Карт', String(d.cards_count)],
    ['Коллекция', d.collection_value.toLocaleString('ru-RU')],
    ['PvP рейтинг', String(d.pvp_rating), 'blue'],
    ['Побед / Поражений', `${d.pvp_wins} / ${d.pvp_losses}`],
    ['Стрик', `${d.daily_streak} дней`, 'yellow'],
    ['Trust', String(d.trust_score)],
    ['Попытки', String(d.daily_attempts)],
    [
      'Indy+',
      d.plus_tier === 'indy_plus' ? 'активен' : 'нет',
      d.plus_tier === 'indy_plus' ? 'gold' : '',
    ],
    [
      'Бан',
      d.ban_level === 'none' ? 'нет' : d.ban_level,
      d.ban_level === 'none' ? 'green' : 'red',
    ],
  ];

  const card = document.createElement('div');
  card.className = 'info-card';

  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.innerHTML = `
    <iconify-icon icon="lucide:user" width="18" height="18"></iconify-icon>
    ПРОФИЛЬ
  `;
  card.appendChild(title);

  for (const [key, value, cls] of rows) {
    const row = document.createElement('div');
    row.className = 'info-row';
    row.innerHTML = `
      <span class="info-row-label">${key}</span>
      <span class="info-row-value ${cls ?? ''}">${value}</span>
    `;
    card.appendChild(row);
  }

  container.appendChild(card);
}

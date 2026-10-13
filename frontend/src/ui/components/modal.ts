/**
 * Универсальная модалка снизу.
 */

export interface ModalAction {
  label: string;
  icon?: string;
  variant?: 'default' | 'primary' | 'danger';
  onClick: () => void | Promise<void>;
}

export class Modal {
  private overlay: HTMLElement;
  private contentEl: HTMLElement;

  constructor() {
    this.overlay = document.createElement('div');
    this.overlay.className = 'modal-overlay';

    const modal = document.createElement('div');
    modal.className = 'modal';

    const handle = document.createElement('div');
    handle.className = 'modal-handle';

    this.contentEl = document.createElement('div');
    this.contentEl.className = 'modal-content';

    modal.appendChild(handle);
    modal.appendChild(this.contentEl);
    this.overlay.appendChild(modal);

    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) this.close();
    });

    document.body.appendChild(this.overlay);
  }

  open(): void {
    this.overlay.classList.add('visible');
  }

  close(): void {
    this.overlay.classList.remove('visible');
    this.contentEl.innerHTML = '';
  }

  showCard(
    card: {
      id: number;
      name: string;
      rarity: string;
      team: string | null;
      year: number | null;
      price: number;
      image_url: string | null;
      count: number;
    },
    actions: ModalAction[],
  ): void {
    const rarityLabels: Record<string, string> = {
      basic: 'Basic',
      rare: 'Rare',
      epic: 'Epic',
      mythic: 'Mythic',
      legendary: 'Legendary',
      limited: 'Limited',
      season: 'Season',
    };

    const imageHtml = card.image_url
      ? `<img src="${card.image_url}" alt="${this.escape(card.name)}" />`
      : '<iconify-icon icon="lucide:car" width="64" height="64"></iconify-icon>';

    this.contentEl.innerHTML = `
      <div class="modal-card-image ${card.rarity}">
        ${imageHtml}
      </div>
      <div class="modal-card-title">
        ${this.escape(card.name)}
      </div>
      <div class="modal-card-meta">
        <span class="modal-card-rarity">${rarityLabels[card.rarity] ?? card.rarity}</span>
        ${card.team ? `<span class="modal-card-team">${this.escape(card.team)}</span>` : ''}
        ${card.year ? `<span class="modal-card-year">${card.year}</span>` : ''}
      </div>
      <div class="modal-card-price">
        💰 ${card.price.toLocaleString('ru-RU')}
      </div>
      ${card.count > 1 ? `<div class="modal-card-count">У тебя: ×${card.count}</div>` : ''}
      <div class="modal-actions"></div>
    `;

    const actionsEl = this.contentEl.querySelector('.modal-actions');
    if (!actionsEl) return;

    for (const action of actions) {
      const btn = document.createElement('button');
      btn.className = `modal-action ${action.variant ?? 'default'}`;
      btn.innerHTML = `
        ${action.icon ? `<iconify-icon icon="${action.icon}" width="16" height="16"></iconify-icon>` : ''}
        <span>${action.label}</span>
      `;

      btn.addEventListener('click', async () => {
        await action.onClick();
      });

      actionsEl.appendChild(btn);
    }

    this.open();
  }

  show(html: string): void {
    this.contentEl.innerHTML = html;
    this.open();
  }

  private escape(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
}

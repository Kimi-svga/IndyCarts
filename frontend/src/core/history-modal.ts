/**
 * Модалка истории команд.
 */

export class HistoryModal {
  private overlay: HTMLElement;
  private listEl: HTMLElement;

  constructor(
    container: HTMLElement,
    private onPick: (command: string) => void,
  ) {
    this.overlay = document.createElement('div');
    this.overlay.className = 'history-modal-overlay';

    const modal = document.createElement('div');
    modal.className = 'history-modal';

    const handle = document.createElement('div');
    handle.className = 'history-modal-handle';

    const title = document.createElement('div');
    title.className = 'history-modal-title';
    title.textContent = 'История команд';

    this.listEl = document.createElement('div');
    this.listEl.className = 'history-modal-list';

    modal.appendChild(handle);
    modal.appendChild(title);
    modal.appendChild(this.listEl);
    this.overlay.appendChild(modal);

    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) this.close();
    });

    container.appendChild(this.overlay);
  }

  open(commands: string[]): void {
    if (commands.length === 0) {
      this.listEl.innerHTML = '<div class="history-modal-empty">История пуста</div>';
    } else {
      this.listEl.innerHTML = commands
        .slice()
        .reverse()
        .map(
          (cmd, i) => `
          <button class="history-modal-item" data-index="${i}" type="button">
            ${this.escapeHtml(cmd)}
          </button>
        `,
        )
        .join('');

      this.listEl.querySelectorAll('.history-modal-item').forEach((el) => {
        el.addEventListener('click', () => {
          const cmd = (el as HTMLElement).textContent?.trim() ?? '';
          this.onPick(cmd);
          this.close();
        });
      });
    }

    this.overlay.classList.add('visible');
  }

  close(): void {
    this.overlay.classList.remove('visible');
  }

  private escapeHtml(text: string): string {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
      } 

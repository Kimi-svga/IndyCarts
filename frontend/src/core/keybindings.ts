/**
 * Keybindings — Ctrl+A/E/U/K/W/L, Ctrl+R.
 */

export interface KeybindingsHandlers {
  onCtrlR: () => void;
  onCtrlL: () => void;
  onTab: () => void;
  onEscape: () => void;
}

export class Keybindings {
  constructor(
    private input: HTMLInputElement,
    private handlers: KeybindingsHandlers,
  ) {}

  attach(): void {
    this.input.addEventListener('keydown', (e) => this.handleKey(e));
  }

  private handleKey(e: KeyboardEvent): void {
    // Ctrl+R — reverse search
    if (e.ctrlKey && e.key === 'r') {
      e.preventDefault();
      this.handlers.onCtrlR();
      return;
    }

    // Ctrl+L — clear screen
    if (e.ctrlKey && e.key === 'l') {
      e.preventDefault();
      this.handlers.onCtrlL();
      return;
    }

    // Ctrl+A — в начало
    if (e.ctrlKey && e.key === 'a') {
      e.preventDefault();
      this.input.setSelectionRange(0, 0);
      return;
    }

    // Ctrl+E — в конец
    if (e.ctrlKey && e.key === 'e') {
      e.preventDefault();
      const len = this.input.value.length;
      this.input.setSelectionRange(len, len);
      return;
    }

    // Ctrl+U — удалить до начала
    if (e.ctrlKey && e.key === 'u') {
      e.preventDefault();
      const pos = this.input.selectionStart || 0;
      this.input.value = this.input.value.slice(pos);
      this.input.setSelectionRange(0, 0);
      return;
    }

    // Ctrl+K — удалить до конца
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      const pos = this.input.selectionStart || 0;
      this.input.value = this.input.value.slice(0, pos);
      return;
    }

    // Ctrl+W — удалить слово назад
    if (e.ctrlKey && e.key === 'w') {
      e.preventDefault();
      const value = this.input.value;
      const pos = this.input.selectionStart || 0;
      const before = value.slice(0, pos);
      const match = before.match(/\S+\s*$/);

      if (match) {
        this.input.value = value.slice(0, pos - match[0].length) + value.slice(pos);
      }
      return;
    }

    // Tab — автодополнение
    if (e.key === 'Tab') {
      e.preventDefault();
      this.handlers.onTab();
      return;
    }

    // Escape
    if (e.key === 'Escape') {
      this.handlers.onEscape();
      return;
    }
  }
}

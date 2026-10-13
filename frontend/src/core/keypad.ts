/**
 * Keypad — панель кнопок для мобильных.
 * Заменяет Ctrl/Alt/Tab/стрелки.
 */

export type KeypadAction =
  | { type: 'history-prev' }
  | { type: 'history-next' }
  | { type: 'tab' }
  | { type: 'esc' }
  | { type: 'ctrl'; key: string }
  | { type: 'char'; value: string }
  | { type: 'history' }
  | { type: 'clear' };

interface KeypadButton {
  label: string;
  action: KeypadAction;
  longPress?: KeypadAction;
  wide?: boolean;
}

export class Keypad {
  private ctrlActive = false;
  private ctrlTimeout?: number;

  private buttons: KeypadButton[][] = [
    [
      { label: '↑', action: { type: 'history-prev' }, longPress: { type: 'history' } },
      { label: '↓', action: { type: 'history-next' } },
      { label: 'Tab', action: { type: 'tab' } },
      { label: 'Esc', action: { type: 'esc' }, longPress: { type: 'clear' } },
      { label: 'Ctrl', action: { type: 'ctrl', key: '' } },
    ],
    [
      { label: '@', action: { type: 'char', value: '@' } },
      { label: '-', action: { type: 'char', value: '-' } },
      { label: '/', action: { type: 'char', value: '/' } },
      { label: ':', action: { type: 'char', value: ':' } },
      { label: '.', action: { type: 'char', value: '.' } },
      { label: '"', action: { type: 'char', value: '"' } },
      { label: '=', action: { type: 'char', value: '=' } },
      { label: '|', action: { type: 'char', value: '|' } },
    ],
  ];

  constructor(
    private container: HTMLElement,
    private onAction: (action: KeypadAction) => void,
  ) {
    this.render();
  }

  private render(): void {
    const el = document.createElement('div');
    el.className = 'keypad';

    for (const row of this.buttons) {
      const rowEl = document.createElement('div');
      rowEl.className = 'keypad-row';

      for (const btn of row) {
        const buttonEl = document.createElement('button');
        buttonEl.className = 'keypad-btn';
        buttonEl.textContent = btn.label;
        buttonEl.type = 'button';

        let pressTimer: number | undefined;

        const startPress = (e: Event) => {
          e.preventDefault();
          pressTimer = window.setTimeout(() => {
            if (btn.longPress) {
              this.onAction(btn.longPress);
              if (navigator.vibrate) navigator.vibrate(20);
            }
            pressTimer = undefined;
          }, 500);
        };

        const endPress = (e: Event) => {
          e.preventDefault();
          if (pressTimer) {
            clearTimeout(pressTimer);
            pressTimer = undefined;
            this.handlePress(btn);
          }
        };

        buttonEl.addEventListener('touchstart', startPress, { passive: false });
        buttonEl.addEventListener('touchend', endPress, { passive: false });
        buttonEl.addEventListener('mousedown', startPress);
        buttonEl.addEventListener('mouseup', endPress);
        buttonEl.addEventListener('mouseleave', () => {
          if (pressTimer) {
            clearTimeout(pressTimer);
            pressTimer = undefined;
          }
        });

        rowEl.appendChild(buttonEl);
      }

      el.appendChild(rowEl);
    }

    this.container.appendChild(el);
  }

  private handlePress(btn: KeypadButton): void {
    // Ctrl + char = комбинация
    if (this.ctrlActive && btn.action.type === 'char') {
      const ctrlKey = btn.action.value.toLowerCase();
      this.onAction({ type: 'ctrl', key: ctrlKey });
      this.ctrlActive = false;
      this.updateCtrlButton(false);
      if (navigator.vibrate) navigator.vibrate(10);
      return;
    }

    // Активация Ctrl
    if (btn.action.type === 'ctrl') {
      this.ctrlActive = !this.ctrlActive;
      this.updateCtrlButton(this.ctrlActive);

      if (this.ctrlTimeout) clearTimeout(this.ctrlTimeout);
      if (this.ctrlActive) {
        this.ctrlTimeout = window.setTimeout(() => {
          this.ctrlActive = false;
          this.updateCtrlButton(false);
        }, 3000);
      }
      return;
    }

    this.onAction(btn.action);
    if (navigator.vibrate) navigator.vibrate(10);
  }

  private updateCtrlButton(active: boolean): void {
    const btns = this.container.querySelectorAll('.keypad-btn');
    for (const btn of Array.from(btns)) {
      if (btn.textContent === 'Ctrl') {
        btn.classList.toggle('active', active);
      }
    }
  }
       } 

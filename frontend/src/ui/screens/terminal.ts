/**
 * Экран терминала (открывается из header).
 */

import { Terminal } from '@/core/terminal';
import { registerCommands } from '@/commands';

export function renderTerminal(container: HTMLElement): void {
  const windowEl = document.createElement('div');
  windowEl.className = 'term-window';
  windowEl.innerHTML = `
    <div class="term-titlebar">
      <div class="term-dots">
        <span class="dot red"></span>
        <span class="dot yellow"></span>
        <span class="dot green"></span>
      </div>
      <div class="term-title">root@indycarts: ~ — bash</div>
    </div>
  `;
  container.appendChild(windowEl);

  const terminal = new Terminal(windowEl, {
    prompt: 'root@indycarts:~#',
    greeting: `
      <div class="term-brand">
        <span class="term-brand-name">VISUAL</span>
        <span class="term-brand-accent">MERGE</span>
      </div>
      <div class="term-hint">
        Введи <span class="tok-cmd">help</span> для списка команд.
      </div>
    `,
  });

  registerCommands(terminal);

  // Контекст уже установлен глобально
  const globalTerminal = (window as unknown as {
    __vm_terminal?: Terminal;
  }).__vm_terminal;

  if (globalTerminal) {
    // Копируем контекст
    const ctx = (globalTerminal as unknown as {
      options?: { context?: unknown };
    }).options?.context;
    if (ctx) {
      terminal.setContext(ctx as never);
    }
  }
} 

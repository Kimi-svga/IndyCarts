/**
 * Ядро терминала Visual Merge.
 * Ввод, вывод, история, автодополнение, keypad для мобильных.
 */

import type { Command, CommandContext } from '@/types/command';
import { Registry } from './registry';
import { Renderer } from './renderer';
import { History } from './history';
import { Completer } from './completer';
import { Keybindings } from './keybindings';
import { Executor } from './executor';
import { parse } from './parser';
import { Keypad, type KeypadAction } from './keypad';
import { HistoryModal } from './history-modal';

export interface TerminalOptions {
  prompt?: string;
  greeting?: string;
  onCommand?: (command: string) => void;
  context?: Omit<CommandContext, 'args' | 'flags' | 'input'>;
}

export class Terminal {
  private registry = new Registry();
  private renderer = new Renderer();
  private history = new History();
  private completer: Completer;
  private executor: Executor;

  private outputEl: HTMLElement;
  private inputEl: HTMLInputElement;
  private autocompleteEl: HTMLElement;
  private keypad: Keypad;
  private historyModal: HistoryModal;

  private currentCompletions: Array<{ value: string; hint?: string }> = [];

  constructor(
    private container: HTMLElement,
    private options: TerminalOptions = {},
  ) {
    this.completer = new Completer(this.registry);
    this.executor = new Executor(this.registry);

    // ─── Input ───
    this.inputEl = document.createElement('input');
    this.inputEl.type = 'text';
    this.inputEl.className = 'term-input';
    this.inputEl.autocomplete = 'off';
    this.inputEl.autocapitalize = 'off';
    this.inputEl.spellcheck = false;
    this.inputEl.setAttribute('autocorrect', 'off');
    this.inputEl.setAttribute('inputmode', 'text');
    this.inputEl.placeholder = 'введи help...';

    // ─── Output ───
    this.outputEl = document.createElement('div');
    this.outputEl.className = 'term-output';

    // ─── Autocomplete ───
    this.autocompleteEl = document.createElement('div');
    this.autocompleteEl.className = 'term-autocomplete';

    // ─── Render ───
    this.render();
    this.attachEvents();

    // ─── Keypad ───
    this.keypad = new Keypad(
      this.container,
      this.handleKeypadAction.bind(this),
    );

    // ─── History Modal ───
    this.historyModal = new HistoryModal(
      this.container,
      (command) => {
        this.inputEl.value = command;
        this.inputEl.focus();
      },
    );

    // ─── Greeting + Focus ───
    this.printGreeting();
    this.inputEl.focus();
  }

  /** Регистрация команд. */
  register(...commands: Command[]): void {
    this.registry.registerAll(commands);
  }

  /** Вывод HTML. */
  print(html: string): void {
    const div = document.createElement('div');
    div.className = 'term-line';
    div.innerHTML = html;
    this.outputEl.appendChild(div);
    this.scrollToBottom();
  }

  /** Очистить экран. */
  clear(): void {
    this.outputEl.innerHTML = '';
  }

  /** Выполнить команду. */
  async run(input: string): Promise<void> {
    const trimmed = input.trim();
    if (!trimmed) return;

    this.history.push(trimmed);
    this.printPrompt(trimmed);
    this.options.onCommand?.(trimmed);

    const pipeline = parse(trimmed);
    if (pipeline.length === 0) return;

    const ctx = this.options.context ?? {
      repo: createDummyRepo(),
      print: (html: string) => this.print(html),
      user: { telegramId: 0, username: 'root', role: 'owner' as const },
    };

    const result = await this.executor.execute(pipeline, ctx);
    const html = this.renderer.render(result);
    if (html) this.print(html);
  }

  /** Фокус на input. */
  focus(): void {
    this.inputEl.focus();
  }

  // ═══════════════════════════════════════════
  // PRIVATE
  // ═══════════════════════════════════════════

  private render(): void {
    this.container.innerHTML = '';
    this.container.classList.add('terminal');

    const inputLine = document.createElement('div');
    inputLine.className = 'term-input-line';

    const prompt = document.createElement('span');
    prompt.className = 'term-prompt';
    prompt.textContent = this.options.prompt ?? 'root@indycarts:~#';

    inputLine.appendChild(prompt);
    inputLine.appendChild(this.inputEl);
    inputLine.appendChild(this.autocompleteEl);

    this.container.appendChild(this.outputEl);
    this.container.appendChild(inputLine);
  }

  private attachEvents(): void {
    this.inputEl.addEventListener('keydown', (e) => {
      void this.handleKey(e);
    });

    const kb = new Keybindings(this.inputEl, {
      onCtrlR: () => this.historyModal.open(this.history.all()),
      onCtrlL: () => this.clear(),
      onTab: () => this.applyAutocomplete(),
      onEscape: () => this.hideAutocomplete(),
    });
    kb.attach();

    this.inputEl.addEventListener('input', () => this.updateAutocomplete());

    this.inputEl.addEventListener('blur', () => {
      setTimeout(() => this.hideAutocomplete(), 200);
    });
  }

  private async handleKey(e: KeyboardEvent): Promise<void> {
    if (e.key === 'Enter') {
      e.preventDefault();
      const value = this.inputEl.value;
      this.inputEl.value = '';
      this.hideAutocomplete();
      await this.run(value);
      return;
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prev = this.history.prev(this.inputEl.value);
      if (prev !== null) this.inputEl.value = prev;
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const next = this.history.next();
      if (next !== null) this.inputEl.value = next;
      return;
    }
  }

  private handleKeypadAction(action: KeypadAction): void {
    switch (action.type) {
      case 'history-prev': {
        const prev = this.history.prev(this.inputEl.value);
        if (prev !== null) this.inputEl.value = prev;
        this.inputEl.focus();
        break;
      }

      case 'history-next': {
        const next = this.history.next();
        if (next !== null) this.inputEl.value = next;
        this.inputEl.focus();
        break;
      }

      case 'tab':
        this.applyAutocomplete();
        this.inputEl.focus();
        break;

      case 'esc':
        this.hideAutocomplete();
        this.inputEl.value = '';
        this.inputEl.focus();
        break;

      case 'ctrl':
        this.handleCtrl(action.key);
        this.inputEl.focus();
        break;

      case 'char':
        this.insertChar(action.value);
        this.inputEl.focus();
        break;

      case 'history':
        this.historyModal.open(this.history.all());
        break;

      case 'clear':
        this.clear();
        this.inputEl.focus();
        break;
    }
  }

  private handleCtrl(key: string): void {
    const input = this.inputEl;
    const start = input.selectionStart ?? 0;
    const end = input.selectionEnd ?? 0;
    const value = input.value;

    switch (key) {
      case 'a': {
        input.setSelectionRange(0, 0);
        break;
      }

      case 'e': {
        const len = value.length;
        input.setSelectionRange(len, len);
        break;
      }

      case 'u': {
        input.value = value.slice(end);
        input.setSelectionRange(0, 0);
        break;
      }

      case 'k': {
        input.value = value.slice(0, start);
        input.setSelectionRange(start, start);
        break;
      }

      case 'w': {
        const before = value.slice(0, start);
        const match = before.match(/\S+\s*$/);
        if (match) {
          const cutStart = start - match[0].length;
          input.value = value.slice(0, cutStart) + value.slice(end);
          input.setSelectionRange(cutStart, cutStart);
        }
        break;
      }

      case 'l': {
        this.clear();
        break;
      }

      case 'r': {
        this.historyModal.open(this.history.all());
        break;
      }
    }
  }

  private insertChar(char: string): void {
    const start = this.inputEl.selectionStart ?? this.inputEl.value.length;
    const end = this.inputEl.selectionEnd ?? this.inputEl.value.length;
    const value = this.inputEl.value;

    this.inputEl.value = value.slice(0, start) + char + value.slice(end);
    this.inputEl.setSelectionRange(start + char.length, start + char.length);
  }

  private updateAutocomplete(): void {
    const completions = this.completer.complete(this.inputEl.value);

    if (completions.length === 0) {
      this.hideAutocomplete();
      return;
    }

    this.currentCompletions = completions;

    this.autocompleteEl.innerHTML = completions
      .map(
        (c, i) => `
        <div class="term-autocomplete-item ${i === 0 ? 'active' : ''}" data-index="${i}">
          <span class="term-autocomplete-value">${c.value}</span>
          ${c.hint ? `<span class="term-autocomplete-hint">${c.hint}</span>` : ''}
        </div>
      `,
      )
      .join('');

    this.autocompleteEl.classList.add('visible');

    this.autocompleteEl
      .querySelectorAll('.term-autocomplete-item')
      .forEach((el) => {
        el.addEventListener('click', () => {
          const idx = parseInt(
            (el as HTMLElement).dataset.index || '0',
            10,
          );
          this.applyCompletion(idx);
        });
      });
  }

  private hideAutocomplete(): void {
    this.autocompleteEl.classList.remove('visible');
    this.currentCompletions = [];
  }

  private applyAutocomplete(): void {
    if (this.currentCompletions.length === 0) return;
    this.applyCompletion(0);
  }

  private applyCompletion(index: number): void {
    const completion = this.currentCompletions[index];
    if (!completion) return;

    this.inputEl.value = this.completer.apply(this.inputEl.value, completion);
    this.hideAutocomplete();
    this.inputEl.focus();
  }

  private printPrompt(command: string): void {
    const prompt = this.options.prompt ?? 'root@indycarts:~#';
    this.print(
      `<span class="term-prompt-inline">${prompt}</span> <span class="term-cmd">${this.escapeHtml(command)}</span>`,
    );
  }

  private printGreeting(): void {
    if (this.options.greeting) {
      this.print(this.options.greeting);
    }
  }

  private scrollToBottom(): void {
    this.outputEl.scrollTop = this.outputEl.scrollHeight;
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
}

// ═══════════════════════════════════════════
// DUMMY REPO (если контекст не передан)
// ═══════════════════════════════════════════

function createDummyRepo(): CommandContext['repo'] {
  return {
    users: {
      find: async () => null,
      search: async () => [],
      list: async () => [],
      ban: async () => {},
      unban: async () => {},
      setBalance: async () => {},
    },
    cards: {
      list: async () => [],
      find: async () => null,
      give: async () => {},
      setPrice: async () => {},
    },
  };
  } 

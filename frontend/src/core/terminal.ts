/**
 * Ядро терминала Visual Merge.
 * Ввод, вывод, история, автодополнение.
 */

import type { Command } from '@/types/command';
import { Registry } from './registry';
import { Renderer } from './renderer';
import { History } from './history';
import { Completer } from './completer';
import { Keybindings } from './keybindings';
import { Executor } from './executor';
import { parse } from './parser';
import { Result } from '@/types/result';

export interface TerminalOptions {
  prompt?: string;
  greeting?: string;
  onCommand?: (command: string) => void;
}

export class Terminal {
  private registry = new Registry();
  private renderer = new Renderer();
  private history = new History();
  private completer: Completer;
  private executor: Executor;

  private outputEl: HTMLElement;
  private inputEl: HTMLInputElement;
  private autocompleteEl: HTMLElement | null = null;

  private currentCompletionIndex = 0;
  private currentCompletions: Array<{ value: string; hint?: string }> = [];

  constructor(
    private container: HTMLElement,
    private options: TerminalOptions = {},
  ) {
    this.completer = new Completer(this.registry);
    this.executor = new Executor(this.registry);

    this.outputEl = document.createElement('div');
    this.outputEl.className = 'term-output';

    this.inputEl = document.createElement('input');
    this.inputEl.type = 'text';
    this.inputEl.className = 'term-input';
    this.inputEl.autocomplete = 'off';
    this.inputEl.autocorrect = 'off';
    this.inputEl.autocapitalize = 'off';
    this.inputEl.spellcheck = false;
    this.inputEl.placeholder = 'введи help...';

    this.render();
    this.attachEvents();
    this.printGreeting();
  }

  /** Регистрация команд. */
  register(...commands: Command[]): void {
    this.registry.registerAll(commands);
  }

  /** Вывод строки. */
  print(html: string): void {
    const div = document.createElement('div');
    div.innerHTML = html;
    this.outputEl.appendChild(div);
    this.scrollToBottom();
  }

  /** Очистить. */
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

    const result = await this.executor.execute(pipeline, {
      repo: this.createDummyRepo(),
      print: (html) => this.print(html),
      user: {
        telegramId: 0,
        username: 'root',
        role: 'owner',
      },
    });

    const html = this.renderer.render(result);
    if (html) this.print(html);
  }

  private render(): void {
    this.container.innerHTML = '';
    this.container.className = 'terminal';

    const inputLine = document.createElement('div');
    inputLine.className = 'term-input-line';

    const prompt = document.createElement('span');
    prompt.className = 'term-prompt';
    prompt.textContent = this.options.prompt ?? 'root@indycarts:~#';

    inputLine.appendChild(prompt);
    inputLine.appendChild(this.inputEl);

    this.container.appendChild(this.outputEl);
    this.container.appendChild(inputLine);

    this.autocompleteEl = document.createElement('div');
    this.autocompleteEl.className = 'term-autocomplete';
    inputLine.appendChild(this.autocompleteEl);
  }

  private attachEvents(): void {
    this.inputEl.addEventListener('keydown', (e) => this.handleKey(e));

    const kb = new Keybindings(this.inputEl, {
      onCtrlR: () => this.openHistoryModal(),
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

  private updateAutocomplete(): void {
    const completions = this.completer.complete(this.inputEl.value);

    if (completions.length === 0) {
      this.hideAutocomplete();
      return;
    }

    this.currentCompletions = completions;
    this.currentCompletionIndex = 0;

    if (!this.autocompleteEl) return;

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

    this.autocompleteEl.querySelectorAll('.term-autocomplete-item').forEach((el) => {
      el.addEventListener('click', () => {
        const idx = parseInt((el as HTMLElement).dataset.index || '0', 10);
        this.applyCompletion(idx);
      });
    });
  }

  private hideAutocomplete(): void {
    this.autocompleteEl?.classList.remove('visible');
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
    this.print(`<span class="term-prompt-inline">${prompt}</span> <span class="term-cmd">${this.escapeHtml(command)}</span>`);
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
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  private openHistoryModal(): void {
    const items = this.history.search('');
    this.print(`<div class="term-history-hint">История (${items.length}):</div>`);
    for (const item of items.slice(-10)) {
      this.print(`<div class="term-history-item">${this.escapeHtml(item)}</div>`);
    }
  }

  private createDummyRepo(): any {
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
} 

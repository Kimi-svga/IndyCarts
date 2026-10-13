/**
 * История команд + поиск по ней.
 */

const MAX_HISTORY = 200;

export class History {
  private commands: string[] = [];
  private index = -1;
  private draft = '';

  constructor() {
    this.load();
  }

  /** Добавить команду. */
  push(command: string): void {
    if (!command.trim()) return;
    if (this.commands[this.commands.length - 1] === command) return;

    this.commands.push(command);
    if (this.commands.length > MAX_HISTORY) {
      this.commands.shift();
    }

    this.index = -1;
    this.save();
  }

  /** Предыдущая команда (↑). */
  prev(current: string): string | null {
    if (this.commands.length === 0) return null;

    if (this.index === -1) {
      this.draft = current;
      this.index = this.commands.length - 1;
    } else if (this.index > 0) {
      this.index--;
    } else {
      return this.commands[this.index];
    }

    return this.commands[this.index];
  }

  /** Следующая команда (↓). */
  next(): string | null {
    if (this.index === -1) return null;

    if (this.index < this.commands.length - 1) {
      this.index++;
      return this.commands[this.index];
    }

    this.index = -1;
    return this.draft;
  }

  /** Все команды. */
  all(): string[] {
    return [...this.commands];
  }

  /** Поиск (Ctrl+R). */
  search(query: string): string[] {
    if (!query) return this.all().slice(-20);
    return this.commands.filter((c) => c.includes(query)).slice(-20);
  }

  /** Очистить. */
  clear(): void {
    this.commands = [];
    this.index = -1;
    this.save();
  }

  private save(): void {
    try {
      localStorage.setItem('vm_history', JSON.stringify(this.commands));
    } catch {
      // ignore
    }
  }

  private load(): void {
    try {
      const raw = localStorage.getItem('vm_history');
      if (raw) {
        this.commands = JSON.parse(raw);
      }
    } catch {
      this.commands = [];
    }
  }
  } 

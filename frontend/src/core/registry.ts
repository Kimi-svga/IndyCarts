/**
 * Реестр команд терминала.
 */

import type { Command } from '@/types/command';

export class Registry {
  private commands = new Map<string, Command>();

  register(command: Command): void {
    this.commands.set(command.name, command);
  }

  registerAll(commands: Command[]): void {
    for (const cmd of commands) {
      this.register(cmd);
    }
  }

  get(name: string): Command | undefined {
    return this.commands.get(name);
  }

  has(name: string): boolean {
    return this.commands.has(name);
  }

  all(): Command[] {
    return Array.from(this.commands.values());
  }

  names(): string[] {
    return Array.from(this.commands.keys()).sort();
  }

  /** Поиск команд по префиксу (для автодополнения). */
  search(prefix: string): Command[] {
    return this.all().filter((cmd) => cmd.name.startsWith(prefix));
  }
}

/**
 * Команда help — список команд и справка по одной.
 */

import type { Command, CommandContext } from '@/types/command';
import { Result } from '@/types/result';
import type { Registry } from '@/core/registry';

export function createHelpCommand(registry: Registry): Command {
  return {
    name: 'help',
    description: 'Список команд или справка по одной',
    usage: 'help [command]',
    examples: ['help', 'help user'],

    async run(ctx: CommandContext) {
      const target = ctx.args[0];

      if (target) {
        const cmd = registry.get(target);
        if (!cmd) {
          return Result.error(`команда не найдена: ${target}`);
        }

        const lines: Array<[string, string, string?]> = [
          ['Команда', cmd.name, 'blue'],
          ['Описание', cmd.description],
        ];

        if (cmd.usage) lines.push(['Использование', cmd.usage, 'yellow']);
        if (cmd.examples) {
          lines.push(['Примеры', cmd.examples.join('<br>')]);
        }

        return Result.kv(lines);
      }

      const commands = registry.all();
      if (commands.length === 0) {
        return Result.warn('команды не зарегистрированы');
      }

      const rows = commands.map((c) => [c.name, c.description]);
      return Result.table(['Команда', 'Описание'], rows);
    },
  };
        } 

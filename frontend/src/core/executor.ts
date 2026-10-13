/**
 * Выполнение команд с поддержкой пайпов.
 */

import type { CommandContext } from '@/types/command';
import type { CommandResult } from '@/types/result';
import { Result } from '@/types/result';
import type { ParsedCommand } from './parser';
import type { Registry } from './registry';

export class Executor {
  constructor(private registry: Registry) {}

  async execute(
    pipeline: ParsedCommand[],
    ctx: Omit<CommandContext, 'args' | 'flags' | 'input'>,
  ): Promise<CommandResult> {
    if (pipeline.length === 0) {
      return Result.empty();
    }

    let input: CommandResult | null = null;

    for (const cmd of pipeline) {
      const handler = this.registry.get(cmd.name);

      if (!handler) {
        return Result.error(`command not found: ${cmd.name}`);
      }

      try {
        input = await handler.run({
          ...ctx,
          args: cmd.args,
          flags: cmd.flags,
          input,
        });
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        return Result.error(`execution failed: ${message}`);
      }
    }

    return input ?? Result.empty();
  }
}

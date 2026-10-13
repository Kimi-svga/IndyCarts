/**
 * Команда clear — очистить экран терминала.
 */

import type { Command } from '@/types/command';
import { Result } from '@/types/result';

export const clearCommand: Command = {
  name: 'clear',
  description: 'Очистить экран',
  usage: 'clear',

  async run() {
    return Result.empty();
  },
};

/**
 * Регистрация всех команд.
 */

import type { Terminal } from '@/core/terminal';
import { createHelpCommand } from './help';
import { userCommand } from './user';
import { cardCommand } from './card';
import { systemCommand } from './system';
import { clearCommand } from './clear';

export function registerCommands(terminal: Terminal): void {
  const helpCommand = createHelpCommand(terminal.getRegistry());

  terminal.register(
    helpCommand,
    userCommand,
    cardCommand,
    systemCommand,
    clearCommand,
  );
} 

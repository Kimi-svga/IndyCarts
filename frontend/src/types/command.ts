/**
 * Типы команд терминала Visual Merge.
 */

import type { CommandResult } from './result';
import type { Repository } from './repo';

/** Контекст выполнения команды. */
export interface CommandContext {
  /** Аргументы (без флагов). */
  args: string[];

  /** Флаги (--key=value или --key). */
  flags: Record<string, string | true>;

  /** Вход из пайпа (результат предыдущей команды). */
  input: CommandResult | null;

  /** Репозиторий данных. */
  repo: Repository;

  /** API для вывода. */
  print: (html: string) => void;

  /** Текущий юзер (админ). */
  user: {
    telegramId: number;
    username: string;
    role: 'owner' | 'admin' | 'moderator' | 'helper' | 'support' | 'player';
  };
}

/** Определение команды. */
export interface Command {
  /** Имя (user, card, system). */
  name: string;

  /** Описание для help. */
  description: string;

  /** Пример использования. */
  usage?: string;

  /** Примеры. */
  examples?: string[];

  /** Минимальная роль. */
  permission?: 'owner' | 'admin' | 'moderator' | 'helper' | 'support' | 'player';

  /** Обработчик. */
  run: (ctx: CommandContext) => Promise<CommandResult>;
}

/** Реестр команд. */
export type CommandRegistry = Map<string, Command>;

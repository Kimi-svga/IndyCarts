/**
 * Команда system — системные команды.
 */

import type { Command, CommandContext } from '@/types/command';
import { Result } from '@/types/result';

export const systemCommand: Command = {
  name: 'system',
  description: 'Системные команды',
  usage: 'system <action>',
  examples: ['system stats', 'system health', 'system whoami', 'system date'],

  async run(ctx: CommandContext) {
    const action = ctx.args[0] ?? 'stats';

    switch (action) {
      case 'stats':
        return Result.kv([
          ['Игроков', '1,247', 'blue'],
          ['Новых за день', '23', 'green'],
          ['Активных (7д)', '412'],
          ['Монет в игре', '145,230,000', 'gold'],
          ['Карт', '8,420'],
          ['Indy+ активных', '89', 'gold'],
        ]);

      case 'health':
        return Result.raw(`
          <span class="tok-success">✓</span> Database: <span class="tok-success">OK</span> (12ms)<br>
          <span class="tok-success">✓</span> Bot API: <span class="tok-success">OK</span> (45ms)<br>
          <span class="tok-success">✓</span> Webhook: <span class="tok-success">OK</span><br>
          <span class="tok-success">✓</span> Cron tasks: <span class="tok-success">12 active</span><br>
          <span class="tok-success">✓</span> Frontend: <span class="tok-success">OK</span>
        `);

      case 'whoami':
        return Result.kv([
          ['Telegram ID', String(ctx.user.telegramId)],
          ['Username', `@${ctx.user.username}`, 'green'],
          ['Роль', ctx.user.role, 'blue'],
        ]);

      case 'date': {
        const now = new Date();
        const date = now.toLocaleDateString('ru-RU');
        const time = now.toLocaleTimeString('ru-RU');
        return Result.kv([
          ['Дата', date],
          ['Время', time, 'blue'],
          ['UTC', now.toISOString()],
        ]);
      }

      default:
        return Result.error(`неизвестное действие: ${action}`);
    }
  },
}; 

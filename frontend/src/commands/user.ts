/**
 * Команда user — управление пользователями.
 */

import type { Command, CommandContext } from '@/types/command';
import { Result } from '@/types/result';

export const userCommand: Command = {
  name: 'user',
  description: 'Управление пользователями',
  usage: 'user <action> [@username] [--flags]',
  examples: [
    'user info @alexpalou',
    'user search --query=alex',
    'user ban @alexpalou --duration=30d --reason="spam"',
    'user unban @alexpalou',
    'user set-balance @alexpalou --amount=100000',
  ],

  async run(ctx: CommandContext) {
    const action = ctx.args[0];

    if (!action) {
      return Result.error(
        'укажи действие: info, search, list, ban, unban, set-balance',
      );
    }

    switch (action) {
      case 'info': {
        const target = ctx.args[1];
        if (!target || !target.startsWith('@')) {
          return Result.error('укажи @username');
        }

        const username = target.slice(1);
        const user = await ctx.repo.users.find(username);

        if (!user) {
          return Result.error(`пользователь ${target} не найден`);
        }

        return Result.kv([
          ['ID', String(user.telegramId), 'blue'],
          ['Username', `@${user.username}`, 'green'],
          ['Баланс', user.balance.toLocaleString('ru-RU'), 'gold'],
          [
            'PvP',
            `${user.pvpRating} (${user.pvpWins}W/${user.pvpLosses}L)`,
          ],
          ['Стрик', `${user.dailyStreak} дней`, 'yellow'],
          ['Trust', String(user.trustScore)],
          [
            'Indy+',
            user.plusTier === 'indy_plus'
              ? user.plusExpiresAt ?? 'активен'
              : 'нет',
            user.plusTier === 'indy_plus' ? 'gold' : '',
          ],
          [
            'Бан',
            user.banLevel === 'none' ? 'нет' : user.banLevel,
            user.banLevel === 'none' ? 'green' : 'red',
          ],
        ]);
      }

      case 'search': {
        const query = String(ctx.flags.query ?? '');
        if (!query) {
          return Result.error('укажи --query=...');
        }

        const users = await ctx.repo.users.search(query);

        if (users.length === 0) {
          return Result.warn(`ничего не найдено по "${query}"`);
        }

        const rows = users.map((u) => [
          `@${u.username}`,
          u.balance.toLocaleString('ru-RU'),
          String(u.pvpRating),
        ]);

        return Result.table(['Username', 'Баланс', 'PvP'], rows);
      }

      case 'list': {
        const plusOnly = ctx.flags.plus === true;
        const limit = Number(ctx.flags.limit ?? 20);

        const users = await ctx.repo.users.list({
          plus: plusOnly,
          limit,
        });

        if (users.length === 0) {
          return Result.warn('пользователей нет');
        }

        const rows = users.map((u) => [
          `@${u.username}`,
          u.balance.toLocaleString('ru-RU'),
          u.plusTier === 'indy_plus' ? '💎' : '—',
        ]);

        return Result.table(['Username', 'Баланс', 'Indy+'], rows);
      }

      case 'ban': {
        const target = ctx.args[1];
        if (!target || !target.startsWith('@')) {
          return Result.error('укажи @username');
        }

        const duration = String(ctx.flags.duration ?? '30d');
        const reason = String(ctx.flags.reason ?? 'без причины');

        const username = target.slice(1);
        const user = await ctx.repo.users.find(username);

        if (!user) {
          return Result.error(`пользователь ${target} не найден`);
        }

        await ctx.repo.users.ban(user.id, duration, reason);

        return Result.success(
          `@${username} забанен на ${duration}. Причина: ${reason}`,
        );
      }

      case 'unban': {
        const target = ctx.args[1];
        if (!target || !target.startsWith('@')) {
          return Result.error('укажи @username');
        }

        const username = target.slice(1);
        const user = await ctx.repo.users.find(username);

        if (!user) {
          return Result.error(`пользователь ${target} не найден`);
        }

        await ctx.repo.users.unban(user.id);

        return Result.success(`@${username} разбанен`);
      }

      case 'set-balance': {
        const target = ctx.args[1];
        if (!target || !target.startsWith('@')) {
          return Result.error('укажи @username');
        }

        const amount = Number(ctx.flags.amount);
        if (!Number.isFinite(amount)) {
          return Result.error('укажи --amount=100000');
        }

        const username = target.slice(1);
        const user = await ctx.repo.users.find(username);

        if (!user) {
          return Result.error(`пользователь ${target} не найден`);
        }

        const oldBalance = user.balance;
        await ctx.repo.users.setBalance(user.id, amount);

        return Result.kv([
          ['Username', `@${username}`, 'green'],
          ['Было', oldBalance.toLocaleString('ru-RU')],
          ['Стало', amount.toLocaleString('ru-RU'), 'gold'],
        ]);
      }

      default:
        return Result.error(`неизвестное действие: ${action}`);
    }
  },
}; 

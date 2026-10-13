/**
 * Команда card — управление картами.
 */

import type { Command, CommandContext } from '@/types/command';
import { Result } from '@/types/result';

export const cardCommand: Command = {
  name: 'card',
  description: 'Управление картами',
  usage: 'card <action> [--flags]',
  examples: [
    'card list --rarity=legendary',
    'card info --id=1',
    'card give @alexpalou --id=1',
    'card set-price --id=1 --price=30000',
  ],

  async run(ctx: CommandContext) {
    const action = ctx.args[0];

    if (!action) {
      return Result.error('укажи действие: list, info, give, set-price');
    }

    switch (action) {
      case 'list': {
        const rarity = ctx.flags.rarity ? String(ctx.flags.rarity) : undefined;
        const limit = Number(ctx.flags.limit ?? 20);

        const cards = await ctx.repo.cards.list({ rarity, limit });

        if (cards.length === 0) {
          return Result.warn('карт нет');
        }

        const rows = cards.map((c) => [
          String(c.id),
          c.name,
          c.rarity,
          c.price.toLocaleString('ru-RU'),
        ]);

        return Result.table(['ID', 'Название', 'Редкость', 'Цена'], rows);
      }

      case 'info': {
        const id = Number(ctx.flags.id);
        if (!Number.isFinite(id)) {
          return Result.error('укажи --id=1');
        }

        const card = await ctx.repo.cards.find(id);

        if (!card) {
          return Result.error(`карта #${id} не найдена`);
        }

        return Result.kv([
          ['ID', String(card.id), 'blue'],
          ['Название', card.name, 'green'],
          ['Редкость', card.rarity],
          ['Команда', card.team ?? '—'],
          ['Год', card.year ? String(card.year) : '—'],
          ['Цена', card.price.toLocaleString('ru-RU'), 'gold'],
          [
            'Тираж',
            card.maxSupply
              ? `${card.issued}/${card.maxSupply}`
              : `${card.issued}/∞`,
          ],
          ['У тебя', `×${card.count}`, 'yellow'],
        ]);
      }

      case 'give': {
        const target = ctx.args[1];
        if (!target || !target.startsWith('@')) {
          return Result.error('укажи @username');
        }

        const cardId = Number(ctx.flags.id);
        if (!Number.isFinite(cardId)) {
          return Result.error('укажи --id=1');
        }

        const username = target.slice(1);
        const user = await ctx.repo.users.find(username);

        if (!user) {
          return Result.error(`пользователь ${target} не найден`);
        }

        const card = await ctx.repo.cards.find(cardId);
        if (!card) {
          return Result.error(`карта #${cardId} не найдена`);
        }

        await ctx.repo.cards.give(user.id, card.id);

        return Result.success(`@${username} выдана карта "${card.name}"`);
      }

      case 'set-price': {
        const id = Number(ctx.flags.id);
        const price = Number(ctx.flags.price);

        if (!Number.isFinite(id)) return Result.error('укажи --id=1');
        if (!Number.isFinite(price)) return Result.error('укажи --price=30000');

        const card = await ctx.repo.cards.find(id);
        if (!card) {
          return Result.error(`карта #${id} не найдена`);
        }

        const oldPrice = card.price;
        await ctx.repo.cards.setPrice(card.id, price);

        return Result.kv([
          ['Карта', card.name, 'green'],
          ['Было', oldPrice.toLocaleString('ru-RU')],
          ['Стало', price.toLocaleString('ru-RU'), 'gold'],
        ]);
      }

      default:
        return Result.error(`неизвестное действие: ${action}`);
    }
  },
}; 

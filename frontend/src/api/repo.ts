/**
 * API Repository — реальный доступ к данным через бэкенд.
 */

import type {
  Card,
  CardRepository,
  Repository,
  User,
  UserRepository,
} from '@/types/repo';
import { apiFetch } from './client';

/** Выполнить команду на сервере. */
async function runCommand(
  command: string,
  args: string[],
  flags: Record<string, string | true>,
): Promise<unknown> {
  const response = await apiFetch<{ result: unknown }>('/api/admin/command', {
    method: 'POST',
    body: JSON.stringify({ command, args, flags }),
  });

  return response.result;
}

// ═══════════════════════════════════════════
// USERS
// ═══════════════════════════════════════════

const usersApi: UserRepository = {
  async find(username: string): Promise<User | null> {
    try {
      const data = (await runCommand('user.info', [username], {})) as User;
      return data ?? null;
    } catch {
      return null;
    }
  },

  async search(query: string): Promise<User[]> {
    try {
      return (await runCommand('user.search', [], { query })) as User[];
    } catch {
      return [];
    }
  },

  async list(filter): Promise<User[]> {
    try {
      const flags: Record<string, string | true> = {};
      if (filter?.plus) flags.plus = true;
      if (filter?.limit) flags.limit = String(filter.limit);

      return (await runCommand('user.list', [], flags)) as User[];
    } catch {
      return [];
    }
  },

  async ban(userId: number, duration: string, reason: string): Promise<void> {
    await runCommand('user.ban', [String(userId)], { duration, reason });
  },

  async unban(userId: number): Promise<void> {
    await runCommand('user.unban', [String(userId)], {});
  },

  async setBalance(userId: number, amount: number): Promise<void> {
    await runCommand('user.set-balance', [String(userId)], {
      amount: String(amount),
    });
  },
};

// ═══════════════════════════════════════════
// CARDS
// ═══════════════════════════════════════════

const cardsApi: CardRepository = {
  async list(filter): Promise<Card[]> {
    try {
      const flags: Record<string, string | true> = {};
      if (filter?.rarity) flags.rarity = filter.rarity;
      if (filter?.limit) flags.limit = String(filter.limit);

      return (await runCommand('card.list', [], flags)) as Card[];
    } catch {
      return [];
    }
  },

  async find(id: number): Promise<Card | null> {
    try {
      return (await runCommand('card.info', [], { id: String(id) })) as Card;
    } catch {
      return null;
    }
  },

  async give(userId: number, cardId: number): Promise<void> {
    await runCommand('card.give', [String(userId)], { id: String(cardId) });
  },

  async setPrice(cardId: number, price: number): Promise<void> {
    await runCommand('card.set-price', [], {
      id: String(cardId),
      price: String(price),
    });
  },
};

// ═══════════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════════

export function createApiRepo(): Repository {
  return {
    users: usersApi,
    cards: cardsApi,
  };
  } 

/**
 * Интерфейс репозитория данных.
 *
 * Абстракция над API. Позволяет:
 * - Использовать API (prod)
 * - Использовать локальные данные (demo)
 * - Использовать mock (tests)
 */

/** Юзер. */
export interface User {
  id: number;
  telegramId: number;
  username: string;
  balance: number;
  pvpRating: number;
  pvpWins: number;
  pvpLosses: number;
  dailyStreak: number;
  trustScore: number;
  plusTier: 'free' | 'indy_plus';
  plusExpiresAt: string | null;
  banLevel: 'none' | 'warn' | 'mute' | 'ban';
}

/** Карта. */
export interface Card {
  id: number;
  name: string;
  rarity: string;
  team: string | null;
  year: number | null;
  price: number;
  imageUrl: string | null;
  count: number;
  maxSupply: number | null;
  issued: number;
}

/** Репозиторий пользователей. */
export interface UserRepository {
  find(username: string): Promise<User | null>;
  search(query: string): Promise<User[]>;
  list(filter?: { plus?: boolean; limit?: number }): Promise<User[]>;
  ban(userId: number, duration: string, reason: string): Promise<void>;
  unban(userId: number): Promise<void>;
  setBalance(userId: number, amount: number): Promise<void>;
}

/** Репозиторий карт. */
export interface CardRepository {
  list(filter?: { rarity?: string; limit?: number }): Promise<Card[]>;
  find(id: number): Promise<Card | null>;
  give(userId: number, cardId: number): Promise<void>;
  setPrice(cardId: number, price: number): Promise<void>;
}

/** Главный репозиторий. */
export interface Repository {
  users: UserRepository;
  cards: CardRepository;
}

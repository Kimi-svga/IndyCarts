/**
 * Типы уведомлений Visual Merge.
 */

export type NotificationType =
  | 'broadcast'
  | 'pvp'
  | 'trade'
  | 'clan'
  | 'auction'
  | 'support'
  | 'system';

export interface Notification {
  id: number;
  type: NotificationType;
  title: string;
  text: string;
  icon: string;         // Lucide icon name без "lucide:"
  color: string;        // "blue" | "orange" | "purple" | "yellow" | "gold" | "green" | "red"
  payload: string | null;
  is_read: boolean;
  created_at: string;   // ISO
}

export interface NotificationsResponse {
  items: Notification[];
  unread: number;
}

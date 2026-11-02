/**
 * Поиск игрока — модалка + API.
 * v2.0
 */

import { Modal } from './modal';
import { apiFetch } from '@/api/client';

interface SearchResult {
  username: string;
  telegram_id: number;
  pvp_rating: number;
  plus_tier: string;
  daily_streak: number;
}

export function openSearchModal(onPick: (username: string) => void): void {
  const modal = new Modal();

  modal.show(`
    <div class="modal-title">🔍 Поиск игрока</div>
    <input
      type="text"
      id="search-query"
      class="search-input"
      placeholder="Введи ник (мин. 2 символа)"
      autocorrect="off"
      autocapitalize="off"
      spellcheck="false"
    />
    <div class="search-results" id="search-results"></div>
  `);

  const input = document.getElementById('search-query') as HTMLInputElement | null;
  const results = document.getElementById('search-results');
  input?.focus();

  let debounceTimer: number | undefined;

  const doSearch = async (query: string) => {
    if (!results) return;

    if (query.trim().length < 2) {
      results.innerHTML = '<div class="search-empty">Введи минимум 2 символа</div>';
      return;
    }

    results.innerHTML = '<div class="search-empty">Поиск...</div>';

    try {
      const list = await apiFetch<SearchResult[]>(
        `/api/users/search?query=${encodeURIComponent(query.trim())}`,
      );

      if (list.length === 0) {
        results.innerHTML = '<div class="search-empty">Никого не нашли</div>';
        return;
      }

      results.innerHTML = list
        .map(
          (u) => `
            <div class="search-result" data-username="${escapeAttr(u.username)}">
              <div class="search-result-avatar">${escapeHtml(u.username[0] ?? '?')}</div>
              <div class="search-result-name">@${escapeHtml(u.username)}</div>
              <div class="search-result-meta">⚔️ ${u.pvp_rating}</div>
            </div>
          `,
        )
        .join('');

      results.querySelectorAll('[data-username]').forEach((el) => {
        el.addEventListener('click', () => {
          const username = (el as HTMLElement).dataset.username;
          if (username) {
            modal.close();
            onPick(username);
          }
        });
      });
    } catch (e) {
      const err = e as { message?: string };
      results.innerHTML = `<div class="search-empty">${escapeHtml(err.message ?? 'Ошибка')}</div>`;
    }
  };

  input?.addEventListener('input', () => {
    if (debounceTimer) window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(() => {
      void doSearch(input.value);
    }, 350);
  });

  // Стартовое сообщение
  if (results) {
    results.innerHTML = '<div class="search-empty">Введи ник для поиска</div>';
  }
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function escapeAttr(text: string): string {
  return text.replace(/[^a-z0-9_-]/gi, '');
    } 

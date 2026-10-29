/**
 * Хранилище настроек (localStorage).
 */

import type { Settings } from '@/types/theme';
import {
  ACCENTS, BACKGROUNDS, DENSITIES, FONT_SIZES, RADII, DEFAULT_SETTINGS,
} from '@/types/theme';

const LS_KEY = 'vm_settings';

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...DEFAULT_SETTINGS, ...parsed };
    }
  } catch {}
  return { ...DEFAULT_SETTINGS };
}

export function saveSettings(settings: Settings): void {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(settings));
  } catch {}
}

export function applySettings(settings: Settings): void {
  const root = document.documentElement;

  // Тема
  if (settings.theme === 'system') {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme', isDark ? 'dark' : 'light');
  } else {
    root.setAttribute('data-theme', settings.theme);
  }

  // Акцент
  const accent = ACCENTS[settings.accent];
  root.style.setProperty('--accent', accent.color);
  root.style.setProperty('--accent-hover', accent.hover);
  root.style.setProperty('--accent-soft', accent.soft);

  // Шрифт
  root.style.setProperty('--font-size-base', FONT_SIZES[settings.fontSize]);

  // Плотность
  const density = DENSITIES[settings.density];
  root.style.setProperty('--space', density.space);
  root.style.setProperty('--space-sm', density.spaceSm);
  root.style.setProperty('--space-lg', density.spaceLg);

  // Радиус
  const radii = RADII[settings.radius];
  root.style.setProperty('--radius', radii.radius);
  root.style.setProperty('--radius-sm', radii.sm);
  root.style.setProperty('--radius-lg', radii.lg);

  // Фон
  const bg = BACKGROUNDS[settings.background];
  root.style.setProperty('--bg', bg.bg);
  root.style.setProperty('--bg-2', bg.bg2);
  root.style.setProperty('--bg-3', bg.bg3);

  // Анимации
  root.setAttribute('data-animations', settings.animations);

  // 👇 ХЭЛЛОУИН
  if (settings.halloween === 'on') {
    document.body.classList.add('halloween');
  } else {
    document.body.classList.remove('halloween');
  }
}

/**
 * Хранилище настроек — localStorage.
 */

export type Theme = 'system' | 'dark' | 'light';
export type Accent = 'red' | 'blue' | 'green' | 'orange' | 'purple' | 'gold';
export type FontSize = 'small' | 'medium' | 'large';
export type Density = 'compact' | 'normal' | 'spacious';
export type Radius = 'sharp' | 'normal' | 'round';
export type Animations = 'on' | 'off';
export type Background = 'asphalt' | 'coal' | 'graphite';

export interface Settings {
  theme: Theme;
  accent: Accent;
  fontSize: FontSize;
  density: Density;
  radius: Radius;
  animations: Animations;
  background: Background;
}

export const DEFAULT_SETTINGS: Settings = {
  theme: 'system',
  accent: 'red',
  fontSize: 'medium',
  density: 'normal',
  radius: 'normal',
  animations: 'on',
  background: 'asphalt',
};

export const ACCENTS: Record<Accent, { color: string; hover: string; soft: string; label: string }> = {
  red:    { color: '#e10600', hover: '#ff1801', soft: 'rgba(225, 6, 0, 0.15)',    label: '🔴 Красный' },
  blue:   { color: '#3b82f6', hover: '#60a5fa', soft: 'rgba(59, 130, 246, 0.15)', label: '🔵 Синий' },
  green:  { color: '#22c55e', hover: '#4ade80', soft: 'rgba(34, 197, 94, 0.15)',  label: '🟢 Зелёный' },
  orange: { color: '#f97316', hover: '#fb923c', soft: 'rgba(249, 115, 22, 0.15)', label: '🟠 Оранжевый' },
  purple: { color: '#8b5cf6', hover: '#a78bfa', soft: 'rgba(139, 92, 246, 0.15)', label: '🟣 Фиолетовый' },
  gold:   { color: '#d4a017', hover: '#eab308', soft: 'rgba(212, 160, 23, 0.15)', label: '🟡 Золотой' },
};

export const FONT_SIZES: Record<FontSize, string> = {
  small: '13px',
  medium: '15px',
  large: '17px',
};

export const DENSITIES: Record<Density, { space: string; spaceSm: string; spaceLg: string }> = {
  compact:  { space: '10px', spaceSm: '6px',  spaceLg: '16px' },
  normal:   { space: '16px', spaceSm: '8px',  spaceLg: '24px' },
  spacious: { space: '22px', spaceSm: '12px', spaceLg: '32px' },
};

export const RADII: Record<Radius, { radius: string; sm: string; lg: string }> = {
  sharp:  { radius: '4px',  sm: '2px',  lg: '6px'  },
  normal: { radius: '10px', sm: '6px',  lg: '16px' },
  round:  { radius: '18px', sm: '12px', lg: '24px' },
};

export const BACKGROUNDS: Record<Background, { bg: string; bg2: string; bg3: string }> = {
  asphalt:  { bg: '#0a0a0a', bg2: '#141416', bg3: '#1a1a1c' },
  coal:     { bg: '#050505', bg2: '#0d0d0d', bg3: '#141414' },
  graphite: { bg: '#111214', bg2: '#181a1d', bg3: '#1f2125' },
};

const STORAGE_KEY = 'vm_settings';

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
    }
  } catch {
    // ignore
  }
  return { ...DEFAULT_SETTINGS };
}

export function saveSettings(s: Settings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  } catch {
    // ignore
  }
}

export function applySettings(s: Settings): void {
  const root = document.documentElement;
  const accent = ACCENTS[s.accent] || ACCENTS.red;

  root.style.setProperty('--accent', accent.color);
  root.style.setProperty('--accent-hover', accent.hover);
  root.style.setProperty('--accent-soft', accent.soft);

  let theme: 'dark' | 'light' = 'dark';
  if (s.theme === 'system') {
    theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  } else {
    theme = s.theme;
  }
  document.documentElement.dataset.theme = theme;

  root.style.setProperty('--font-size-base', FONT_SIZES[s.fontSize] || FONT_SIZES.medium);

  const d = DENSITIES[s.density] || DENSITIES.normal;
  root.style.setProperty('--space', d.space);
  root.style.setProperty('--space-sm', d.spaceSm);
  root.style.setProperty('--space-lg', d.spaceLg);

  const r = RADII[s.radius] || RADII.normal;
  root.style.setProperty('--radius', r.radius);
  root.style.setProperty('--radius-sm', r.sm);
  root.style.setProperty('--radius-lg', r.lg);

  document.documentElement.dataset.animations = s.animations;

  if (theme === 'dark') {
    const b = BACKGROUNDS[s.background] || BACKGROUNDS.asphalt;
    root.style.setProperty('--bg', b.bg);
    root.style.setProperty('--bg-2', b.bg2);
    root.style.setProperty('--bg-3', b.bg3);
  } else {
    root.style.removeProperty('--bg');
    root.style.removeProperty('--bg-2');
    root.style.removeProperty('--bg-3');
  }

  // Telegram colors
  if (window.Telegram?.WebApp) {
    try {
      window.Telegram.WebApp.setHeaderColor(accent.color);
      window.Telegram.WebApp.setBackgroundColor(theme === 'dark' ? '#0a0a0a' : '#fafafa');
    } catch {
      // ignore
    }
  }
}

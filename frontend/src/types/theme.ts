/**
 * Типы темы и настроек Visual Merge.
 */

export type Theme = 'system' | 'dark' | 'light';
export type Accent = 'red' | 'blue' | 'green' | 'orange' | 'purple' | 'gold';
export type FontSize = 'small' | 'medium' | 'large';
export type Density = 'compact' | 'normal' | 'spacious';
export type Radius = 'sharp' | 'normal' | 'round';
export type Background = 'asphalt' | 'coal' | 'graphite';
export type Animations = 'on' | 'off';

// 👇 НОВОЕ
export type HalloweenMode = 'on' | 'off';

export interface Settings {
  theme: Theme;
  accent: Accent;
  fontSize: FontSize;
  density: Density;
  radius: Radius;
  animations: Animations;
  background: Background;
  halloween: HalloweenMode; // 👈 ДОБАВИЛИ
}

export const DEFAULT_SETTINGS: Settings = {
  theme: 'system',
  accent: 'red',
  fontSize: 'medium',
  density: 'normal',
  radius: 'normal',
  animations: 'on',
  background: 'asphalt',
  halloween: 'off', // 👈 ПО УМОЛЧАНИЮ ВЫКЛ
};

export const ACCENTS: Record<Accent, { color: string; hover: string; soft: string }> = {
  red: { color: '#e10600', hover: '#ff1801', soft: 'rgba(225, 6, 0, 0.15)' },
  blue: { color: '#3b82f6', hover: '#60a5fa', soft: 'rgba(59, 130, 246, 0.15)' },
  green: { color: '#22c55e', hover: '#4ade80', soft: 'rgba(34, 197, 94, 0.15)' },
  orange: { color: '#f97316', hover: '#fb923c', soft: 'rgba(249, 115, 22, 0.15)' },
  purple: { color: '#8b5cf6', hover: '#a78bfa', soft: 'rgba(139, 92, 246, 0.15)' },
  gold: { color: '#d4a017', hover: '#eab308', soft: 'rgba(212, 160, 23, 0.15)' },
};

export const FONT_SIZES: Record<FontSize, string> = {
  small: '13px',
  medium: '15px',
  large: '17px',
};

export const DENSITIES: Record<Density, { space: string; spaceSm: string; spaceLg: string }> = {
  compact: { space: '10px', spaceSm: '6px', spaceLg: '16px' },
  normal: { space: '16px', spaceSm: '8px', spaceLg: '24px' },
  spacious: { space: '22px', spaceSm: '12px', spaceLg: '32px' },
};

export const RADII: Record<Radius, { radius: string; sm: string; lg: string }> = {
  sharp: { radius: '4px', sm: '2px', lg: '6px' },
  normal: { radius: '10px', sm: '6px', lg: '16px' },
  round: { radius: '18px', sm: '12px', lg: '24px' },
};

export const BACKGROUNDS: Record<Background, { bg: string; bg2: string; bg3: string }> = {
  asphalt: { bg: '#0d0d0d', bg2: '#141414', bg3: '#1a1a1a' },
  coal: { bg: '#0a0a0a', bg2: '#111111', bg3: '#181818' },
  graphite: { bg: '#111214', bg2: '#181a1d', bg3: '#1f2125' },
}; 

/**
 * Модалка настроек.
 */

import {
  ACCENTS,
  DEFAULT_SETTINGS,
  applySettings,
  loadSettings,
  saveSettings,
  type Accent,
  type Animations,
  type Background,
  type Density,
  type FontSize,
  type Radius,
  type Settings,
  type Theme,
} from './store';

export class SettingsModal {
  private overlay: HTMLElement;
  private content: HTMLElement;
  private settings: Settings;
  private onUpdate: (s: Settings) => void;

  constructor(onUpdate?: (s: Settings) => void) {
    this.settings = loadSettings();
    this.onUpdate = onUpdate ?? (() => {});

    this.overlay = document.createElement('div');
    this.overlay.className = 'settings-overlay';

    const modal = document.createElement('div');
    modal.className = 'settings-modal';

    const handle = document.createElement('div');
    handle.className = 'settings-handle';

    this.content = document.createElement('div');

    modal.appendChild(handle);
    modal.appendChild(this.content);
    this.overlay.appendChild(modal);
    document.body.appendChild(this.overlay);

    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) this.close();
    });
  }

  open(): void {
    this.settings = loadSettings();
    this.render();
    this.overlay.classList.add('visible');
  }

  close(): void {
    this.overlay.classList.remove('visible');
  }

  private set<K extends keyof Settings>(key: K, value: Settings[K]): void {
    this.settings[key] = value;
    saveSettings(this.settings);
    applySettings(this.settings);
    this.onUpdate(this.settings);
    this.render();
  }

  private render(): void {
    const s = this.settings;

    this.content.innerHTML = `
      <div class="settings-title">
        <iconify-icon icon="lucide:settings" width="20" height="20"></iconify-icon>
        ВНЕШНИЙ ВИД
      </div>

      <div class="setting-group">
        <div class="setting-label">Тема</div>
        <div class="setting-options" data-key="theme">
          ${this.option('theme', 'system', 'Системная')}
          ${this.option('theme', 'dark', 'Тёмная')}
          ${this.option('theme', 'light', 'Светлая')}
        </div>
      </div>

      <div class="setting-group">
        <div class="setting-label">Акцент</div>
        <div class="accent-options">
          ${(Object.keys(ACCENTS) as Accent[]).map((a) => `
            <div class="accent-dot ${s.accent === a ? 'active' : ''}"
                 data-accent="${a}"
                 style="background: ${ACCENTS[a].color};"
                 title="${ACCENTS[a].label}">
            </div>
          `).join('')}
        </div>
      </div>

      <div class="setting-group">
        <div class="setting-label">Размер шрифта</div>
        <div class="setting-options" data-key="fontSize">
          ${this.option('fontSize', 'small', 'S')}
          ${this.option('fontSize', 'medium', 'M')}
          ${this.option('fontSize', 'large', 'L')}
        </div>
      </div>

      <div class="setting-group">
        <div class="setting-label">Плотность</div>
        <div class="setting-options" data-key="density">
          ${this.option('density', 'compact', 'Компактно')}
          ${this.option('density', 'normal', 'Обычно')}
          ${this.option('density', 'spacious', 'Просторно')}
        </div>
      </div>

      <div class="setting-group">
        <div class="setting-label">Скругления</div>
        <div class="setting-options" data-key="radius">
          ${this.option('radius', 'sharp', 'Острые')}
          ${this.option('radius', 'normal', 'Обычные')}
          ${this.option('radius', 'round', 'Круглые')}
        </div>
      </div>

      <div class="setting-group">
        <div class="setting-label">Анимации</div>
        <div class="setting-options" data-key="animations">
          ${this.option('animations', 'on', 'Вкл')}
          ${this.option('animations', 'off', 'Выкл')}
        </div>
      </div>

      <div class="setting-group">
        <div class="setting-label">Фон (тёмная тема)</div>
        <div class="setting-options" data-key="background">
          ${this.option('background', 'asphalt', 'Асфальт')}
          ${this.option('background', 'coal', 'Уголь')}
          ${this.option('background', 'graphite', 'Графит')}
        </div>
      </div>

      <button class="settings-reset" id="settings-reset">
        <iconify-icon icon="lucide:rotate-ccw" width="16" height="16"></iconify-icon>
        СБРОСИТЬ
      </button>
    `;

    // Кнопки
    this.content.querySelectorAll<HTMLElement>('.setting-option').forEach((btn) => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.key as keyof Settings;
        const value = btn.dataset.value as string;
        this.set(key, value as never);
      });
    });

    // Акценты
    this.content.querySelectorAll<HTMLElement>('.accent-dot').forEach((dot) => {
      dot.addEventListener('click', () => {
        const accent = dot.dataset.accent as Accent;
        this.set('accent', accent);
      });
    });

    // Сброс
    document.getElementById('settings-reset')?.addEventListener('click', () => {
      this.settings = { ...DEFAULT_SETTINGS };
      saveSettings(this.settings);
      applySettings(this.settings);
      this.onUpdate(this.settings);
      this.render();
    });
  }

  private option(key: keyof Settings, value: string, label: string): string {
    const current = this.settings[key];
    const active = current === value ? 'active' : '';
    return `
      <button class="setting-option ${active}"
              data-key="${key}"
              data-value="${value}">
        ${label}
      </button>
    `;
  }
}

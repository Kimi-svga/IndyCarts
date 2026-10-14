/**
 * Простой роутер для экранов.
 */

export type ScreenName =
  | 'menu'
  | 'profile'
  | 'collection'
  | 'drop'
  | 'market'
  | 'pvp'
  | 'bank'
  | 'shop'
  | 'auction'
  | 'clan'
  | 'rating'
  | 'ref'
  | 'plus'
  | 'terminal';

type ScreenHandler = (container: HTMLElement) => void | Promise<void>;

export class Router {
  private screens = new Map<ScreenName, ScreenHandler>();
  private current: ScreenName | null = null;
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
  }

  register(name: ScreenName, handler: ScreenHandler): void {
    this.screens.set(name, handler);
  }

  async navigate(name: ScreenName): Promise<void> {
    const handler = this.screens.get(name);
    if (!handler) {
      console.warn(`[router] screen not found: ${name}`);
      return;
    }

    this.current = name;
    this.container.innerHTML = '';

    const screenEl = document.createElement('div');
    screenEl.className = 'screen active';
    screenEl.dataset.screen = name;
    this.container.appendChild(screenEl);

    await handler(screenEl);

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  getCurrent(): ScreenName | null {
    return this.current;
  }
  } 

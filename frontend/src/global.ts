/**
 * Visual Merge — глобальные стили.
 * IndyCar Paddock · Design by Expo
 */

:root {
  /* Акцент */
  --accent: #e10600;
  --accent-hover: #ff1801;
  --accent-soft: rgba(225, 6, 0, 0.15);

  /* Фон */
  --bg: #0d0d0d;
  --bg-2: #141414;
  --bg-3: #1a1a1a;

  /* Текст */
  --text: #fafafa;
  --text-dim: #a0a0a0;
  --text-mute: #666;

  /* Границы */
  --line: #262626;
  --line-2: #333;

  /* Редкости */
  --gold: #d4a017;
  --silver: #c0c0c0;
  --bronze: #cd7f32;
  --green: #22c55e;
  --blue: #3b82f6;
  --purple: #8b5cf6;
  --orange: #f97316;
  --yellow: #eab308;
  --red-rare: #ef4444;

  /* Терминал */
  --term-bg: rgba(20, 20, 20, 0.92);
  --term-prompt: #22c55e;
  --term-cmd: #fafafa;
  --term-arg: #60a5fa;
  --term-flag: #fbbf24;
  --term-value: #a78bfa;
  --term-string: #86efac;
  --term-error: #ef4444;
  --term-success: #22c55e;
  --term-warn: #f97316;
  --term-dim: #6b7280;

  /* Шрифты */
  --font-head: 'Unbounded', sans-serif;
  --font-body: 'Onest', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Радиусы */
  --radius: 10px;
  --radius-sm: 6px;

  /* Анимации */
  --transition: 0.15s ease;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
}

html,
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.5;
  min-height: 100vh;
  overflow: hidden;
  overscroll-behavior: none;
}

body {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
}

#app {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

iconify-icon {
  display: inline-block;
  vertical-align: middle;
}

::-webkit-scrollbar {
  width: 4px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--line-2);
  border-radius: 2px;
    } 

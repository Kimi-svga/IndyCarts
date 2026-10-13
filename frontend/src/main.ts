/**
 * Visual Merge — точка входа.
 */

import './styles/global.css';
import './styles/terminal.css';

import { Terminal } from '@/core/terminal';
import { registerCommands } from '@/commands';

const app = document.getElementById('app');
if (!app) {
  throw new Error('#app not found');
}

// Telegram WebApp init
if (window.Telegram?.WebApp) {
  window.Telegram.WebApp.ready();
  window.Telegram.WebApp.expand();
  window.Telegram.WebApp.setHeaderColor('#0d0d0d');
  window.Telegram.WebApp.setBackgroundColor('#0d0d0d');
}

// Приветствие
const greeting = `
  <div class="term-brand">
    <div class="term-brand-title">
      VISUAL <span>MERGE</span>
    </div>
    <div class="term-brand-sub">
      IndyCarts Engine · Design by Expo
    </div>
  </div>
  <div class="term-boot">
    <div><span class="ok">[OK]</span> database</div>
    <div><span class="ok">[OK]</span> bot_api</div>
    <div><span class="ok">[OK]</span> webhook</div>
    <div><span class="ok">[OK]</span> terminal</div>
    <div><span class="ok">[OK]</span> commands</div>
  </div>
  <div class="term-hint">
    Введи <span class="tok-cmd">help</span> для списка команд.
  </div>
`;

// Создаём терминал
const terminal = new Terminal(app, {
  prompt: 'root@indycarts:~#',
  greeting,
});

// Регистрируем команды
registerCommands(terminal); 

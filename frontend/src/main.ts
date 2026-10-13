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

// Приветствие (компактное, без лишних отступов)
const greeting = `
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

// Создаём окно терминала
const windowEl = document.createElement('div');
windowEl.className = 'term-window';
windowEl.innerHTML = `
  <div class="term-titlebar">
    <div class="term-dots">
      <span class="dot red"></span>
      <span class="dot yellow"></span>
      <span class="dot green"></span>
    </div>
    <div class="term-title">root@indycarts: ~ — bash</div>
  </div>
`;
app.appendChild(windowEl);

// Терминал внутри окна
const terminal = new Terminal(windowEl, {
  prompt: 'root@indycarts:~#',
  greeting,
});

registerCommands(terminal);

// Подпись внизу
const credit = document.createElement('div');
credit.className = 'design-credit';
credit.textContent = 'Design by Expo';
app.appendChild(credit); 

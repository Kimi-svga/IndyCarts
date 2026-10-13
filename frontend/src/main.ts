// frontend/src/main.ts
const app = document.getElementById('app')!;

app.innerHTML = `
  <div style="
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background: #0d0d0d;
    color: #fafafa;
    font-family: 'Unbounded', sans-serif;
    padding: 24px;
    text-align: center;
  ">
    <h1 style="font-size: 32px; letter-spacing: 2px; margin-bottom: 8px;">
      VISUAL <span style="color: #e10600;">MERGE</span>
    </h1>
    <p style="color: #666; font-size: 13px; font-family: 'JetBrains Mono', monospace;">
      loading...
    </p>
  </div>
`;

if (window.Telegram?.WebApp) {
  window.Telegram.WebApp.ready();
  window.Telegram.WebApp.expand();
} 

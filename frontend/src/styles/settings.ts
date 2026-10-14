/**
 * Visual Merge — стили модалки настроек.
 */

.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 350;
  display: none;
  align-items: flex-end;
  justify-content: center;
}

.settings-overlay.visible {
  display: flex;
}

.settings-modal {
  background: var(--bg-2, rgba(28, 28, 30, 0.98));
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg, 16px) var(--radius-lg, 16px) 0 0;
  padding: var(--space, 16px);
  padding-bottom: max(var(--space, 16px), env(safe-area-inset-bottom));
  width: 100%;
  max-width: 600px;
  max-height: 85vh;
  overflow-y: auto;
  animation: slideUp 0.25s ease;
}

.settings-handle {
  width: 40px;
  height: 4px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  margin: 0 auto 16px;
}

.settings-title {
  font-family: var(--font-head);
  font-size: 16px;
  font-weight: 700;
  color: var(--text, #fafafa);
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.setting-group {
  margin-bottom: 20px;
}

.setting-label {
  font-family: var(--font-head);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--text-mute, rgba(255, 255, 255, 0.4));
  text-transform: uppercase;
  margin-bottom: 8px;
}

.setting-options {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.setting-option {
  flex: 1;
  min-width: 60px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-sm, 6px);
  color: var(--text-dim, rgba(255, 255, 255, 0.6));
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: center;
}

.setting-option:active {
  transform: scale(0.96);
}

.setting-option.active {
  background: var(--accent-soft, rgba(225, 6, 0, 0.15));
  border-color: var(--accent, #e10600);
  color: var(--accent, #e10600);
  font-weight: 600;
}

.accent-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.accent-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.15);
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.accent-dot:active {
  transform: scale(0.9);
}

.accent-dot.active {
  border-color: var(--text, #fafafa);
  box-shadow: 0 0 0 2px var(--bg-2, #1c1c1e), 0 0 0 4px var(--text, #fafafa);
}

.settings-reset {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: var(--radius, 10px);
  color: #ef4444;
  font-family: var(--font-head);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-top: 12px;
}

.settings-reset:active {
  background: rgba(239, 68, 68, 0.1);
  transform: scale(0.98);
}

/* ─── Отключение анимаций ─── */

html[data-animations="off"] * {
  animation: none !important;
  transition: none !important;
    } 

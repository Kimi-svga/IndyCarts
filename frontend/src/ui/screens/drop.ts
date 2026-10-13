/**
 * Дроп карт — заглушка.
 */

export function renderDrop(container: HTMLElement): void {
  const empty = document.createElement('div');
  empty.className = 'empty-state';
  empty.innerHTML = `
    <iconify-icon icon="lucide:gift" width="64" height="64"></iconify-icon>
    <div class="empty-text">ДРОП</div>
    <div class="empty-sub">Скоро — анимация + результат</div>
  `;
  container.appendChild(empty);
}

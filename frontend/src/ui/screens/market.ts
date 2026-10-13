/**
 * Биржа — заглушка.
 */

export function renderMarket(container: HTMLElement): void {
  const empty = document.createElement('div');
  empty.className = 'empty-state';
  empty.innerHTML = `
    <iconify-icon icon="lucide:trending-up" width="64" height="64"></iconify-icon>
    <div class="empty-text">БИРЖА</div>
    <div class="empty-sub">Скоро — покупка и продажа</div>
  `;
  container.appendChild(empty);
}

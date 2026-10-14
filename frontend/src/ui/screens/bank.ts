/**
 * Банк — кредиты, trust score, погашение.
 */

import { apiFetch } from '@/api/client';
import { Modal } from '../components/modal';

interface ActiveLoan {
  id: number;
  principal: number;
  rate: number;
  total_due: number;
  paid: number;
  remaining: number;
  due_at: string;
  days_left: number;
  status: string;
}

interface BankInfo {
  balance: number;
  trust_score: number;
  trust_rank: string;
  max_loan: number;
  active_loan: ActiveLoan | null;
}

export async function renderBank(container: HTMLElement): Promise<void> {
  const title = document.createElement('div');
  title.className = 'info-card-title';
  title.style.padding = '0 4px';
  title.innerHTML = `
    <iconify-icon icon="lucide:landmark" width="18" height="18"></iconify-icon>
    P4/9 BANK
  `;
  container.appendChild(title);

  const content = document.createElement('div');
  container.appendChild(content);

  const render = async () => {
    content.innerHTML = '<div class="empty-state">Загрузка...</div>';

    let info: BankInfo | null = null;
    try {
      info = await apiFetch<BankInfo>('/api/bank/info');
    } catch (e) {
      content.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
      return;
    }

    if (!info) return;

    const loan = info.active_loan;

    let loanHtml = '';
    if (loan) {
      const warn =
        loan.status === 'overdue'
          ? '<div class="bank-warning">⚠️ ПРОСРОЧКА!</div>'
          : loan.days_left <= 3
            ? `<div class="bank-warning">⚠️ Осталось ${loan.days_left} дней!</div>`
            : '';

      loanHtml = `
        <div class="info-card">
          <div class="info-card-title">📋 Активный кредит</div>
          <div class="info-row"><span class="info-row-label">Взято</span><span class="info-row-value">${loan.principal.toLocaleString('ru-RU')}</span></div>
          <div class="info-row"><span class="info-row-label">Ставка</span><span class="info-row-value">${(loan.rate * 100).toFixed(0)}%</span></div>
          <div class="info-row"><span class="info-row-label">К возврату</span><span class="info-row-value">${loan.total_due.toLocaleString('ru-RU')}</span></div>
          <div class="info-row"><span class="info-row-label">Осталось</span><span class="info-row-value gold">${loan.remaining.toLocaleString('ru-RU')}</span></div>
          <div class="info-row"><span class="info-row-label">До</span><span class="info-row-value">${loan.due_at.slice(0, 10)}</span></div>
          ${warn}
        </div>
      `;
    } else {
      loanHtml = `
        <div class="info-card">
          <div class="info-card-title">💵 Взять кредит</div>
          <div class="info-row"><span class="info-row-label">Лимит</span><span class="info-row-value gold">${info.max_loan.toLocaleString('ru-RU')}</span></div>
          <div class="info-row"><span class="info-row-label">Ставка</span><span class="info-row-value">15–30%</span></div>
          <div class="info-row"><span class="info-row-label">Срок</span><span class="info-row-value">7–45 дней</span></div>
        </div>
      `;
    }

    content.innerHTML = `
      <div class="info-card">
        <div class="info-card-title">
          <iconify-icon icon="lucide:wallet" width="18" height="18"></iconify-icon>
          Баланс
        </div>
        <div class="info-row"><span class="info-row-label">Деньги</span><span class="info-row-value gold">${info.balance.toLocaleString('ru-RU')}</span></div>
        <div class="info-row"><span class="info-row-label">Trust score</span><span class="info-row-value">${info.trust_score} · ${info.trust_rank}</span></div>
      </div>

      ${loanHtml}

      <div class="bank-actions">
        ${
          loan
            ? `
              <button class="bank-btn primary" id="bank-repay">
                <iconify-icon icon="lucide:coins" width="18" height="18"></iconify-icon>
                ПОГАСИТЬ
              </button>
            `
            : `
              <button class="bank-btn primary" id="bank-loan">
                <iconify-icon icon="lucide:landmark" width="18" height="18"></iconify-icon>
                ВЗЯТЬ КРЕДИТ
              </button>
            `
        }
      </div>
    `;

    document.getElementById('bank-loan')?.addEventListener('click', () => {
      openLoanModal(info!.max_loan, render);
    });

    document.getElementById('bank-repay')?.addEventListener('click', () => {
      openRepayModal(loan!.remaining, render);
    });
  };

  await render();
}

function openLoanModal(maxLoan: number, onUpdate: () => void): void {
  const modal = new Modal();

  modal.show(`
    <div class="modal-title">💵 Взять кредит</div>
    <div class="modal-subtitle">Максимум: ${maxLoan.toLocaleString('ru-RU')}</div>
    <input type="number" id="loan-amount" class="modal-input" placeholder="50000" />
    <div class="modal-actions">
      <button class="modal-action primary" id="loan-confirm">Взять</button>
      <button class="modal-action default" id="loan-cancel">Отмена</button>
    </div>
  `);

  const input = document.getElementById('loan-amount') as HTMLInputElement | null;
  input?.focus();

  document.getElementById('loan-cancel')?.addEventListener('click', () => modal.close());
  document.getElementById('loan-confirm')?.addEventListener('click', async () => {
    const amount = parseInt(input?.value ?? '0', 10);
    if (!amount || amount < 1000) {
      showToast('Минимум 1 000', 'error');
      return;
    }

    try {
      const res = await apiFetch<{ ok: boolean; amount: number; total_due: number }>(
        '/api/bank/loan',
        { method: 'POST', body: JSON.stringify({ amount }) },
      );
      modal.close();
      showToast(`✅ Кредит: +${res.amount.toLocaleString('ru-RU')}`, 'success');
      onUpdate();
    } catch (e) {
      const err = e as { message?: string };
      showToast(err.message ?? 'Ошибка', 'error');
    }
  });
}

function openRepayModal(remaining: number, onUpdate: () => void): void {
  const modal = new Modal();

  modal.show(`
    <div class="modal-title">💰 Погасить кредит</div>
    <div class="modal-subtitle">Остаток: ${remaining.toLocaleString('ru-RU')}</div>
    <input type="number" id="repay-amount" class="modal-input" placeholder="${remaining}" />
    <div class="modal-actions">
      <button class="modal-action primary" id="repay-full">Погасить всё</button>
      <button class="modal-action default" id="repay-part">Часть</button>
      <button class="modal-action default" id="repay-cancel">Отмена</button>
    </div>
  `);

  const input = document.getElementById('repay-amount') as HTMLInputElement | null;

  document.getElementById('repay-cancel')?.addEventListener('click', () => modal.close());

  document.getElementById('repay-full')?.addEventListener('click', async () => {
    await doRepay(remaining, modal, onUpdate);
  });

  document.getElementById('repay-part')?.addEventListener('click', async () => {
    const amount = parseInt(input?.value ?? '0', 10);
    if (!amount || amount <= 0) {
      showToast('Введи сумму', 'error');
      return;
    }
    await doRepay(amount, modal, onUpdate);
  });
}

async function doRepay(amount: number, modal: Modal, onUpdate: () => void): Promise<void> {
  try {
    const res = await apiFetch<{ ok: boolean; amount: number; closes_loan: boolean; trust_msg: string }>(
      '/api/bank/repay',
      { method: 'POST', body: JSON.stringify({ amount }) },
    );
    modal.close();
    const msg = res.closes_loan ? `✅ Кредит закрыт! ${res.trust_msg}` : `✅ Погашено ${res.amount.toLocaleString('ru-RU')}`;
    showToast(msg, 'success');
    onUpdate();
  } catch (e) {
    const err = e as { message?: string };
    showToast(err.message ?? 'Ошибка', 'error');
  }
}

function showToast(text: string, type: 'success' | 'error' | 'info'): void {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = text;
  document.body.appendChild(el);

  setTimeout(() => el.classList.add('visible'), 10);
  setTimeout(() => {
    el.classList.remove('visible');
    setTimeout(() => el.remove(), 300);
  }, 3000);
} 

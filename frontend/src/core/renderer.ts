/**
 * Рендер результатов команд в HTML.
 */

import type { CommandResult } from '@/types/result';

export class Renderer {
  render(result: CommandResult): string {
    switch (result.type) {
      case 'text':
        return this.renderText(result.text, result.className);
      case 'kv':
        return this.renderKV(result.data);
      case 'table':
        return this.renderTable(result.headers, result.rows);
      case 'json':
        return this.renderJSON(result.data);
      case 'box':
        return this.renderBox(result.content, result.variant);
      case 'error':
        return this.renderBox(result.message, 'error');
      case 'success':
        return this.renderBox(result.message, 'success');
      case 'warn':
        return this.renderBox(result.message, 'warn');
      case 'raw':
        return result.html;
      case 'empty':
        return '';
    }
  }

  private renderText(text: string, className = ''): string {
    return `<div class="line ${className}">${text}</div>`;
  }

  private renderKV(data: Array<[string, string, string?]>): string {
    const rows = data
      .map(
        ([key, value, cls = '']) =>
          `<div class="kv-row">
            <div class="kv-key">${key}</div>
            <div class="kv-val ${cls}">${value}</div>
          </div>`,
      )
      .join('');
    return `<div class="kv-block">${rows}</div>`;
  }

  private renderTable(headers: string[], rows: string[][]): string {
    const thead = headers.map((h) => `<th>${h}</th>`).join('');
    const tbody = rows
      .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join('')}</tr>`)
      .join('');

    return `<table class="term-table">
      <thead><tr>${thead}</tr></thead>
      <tbody>${tbody}</tbody>
    </table>`;
  }

  private renderJSON(data: unknown): string {
    const json = JSON.stringify(data, null, 2);
    return `<pre class="json-block">${this.escapeHtml(json)}</pre>`;
  }

  private renderBox(content: string, variant: string): string {
    return `<div class="output-box ${variant}">${content}</div>`;
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
    } 

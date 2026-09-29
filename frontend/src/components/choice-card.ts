import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/** A clear selectable action used for the two ways a design can begin. */
@customElement('aerofoil-choice-card')
export class ChoiceCard extends LitElement {
  @property({ type: String }) heading = '';
  @property({ type: String }) detail = '';
  @property({ type: Boolean }) disabled = false;

  override render() {
    return html`
      <button ?disabled=${this.disabled}>
        <span class="heading">${this.heading}</span>
        <span class="detail">${this.detail}</span>
        <span class="action"><slot name="action">Choose this path</slot></span>
      </button>
    `;
  }

  static override styles = css`
    :host {
      display: block;
    }

    button {
      width: 100%;
      min-height: 13.5rem;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      color: var(--ink);
      padding: var(--space-4);
      text-align: left;
      cursor: pointer;
      transition: border-color 120ms ease, background-color 120ms ease;
    }

    button:hover:not(:disabled) {
      border-color: var(--action);
      background: #f3f8f5;
    }

    button:focus-visible {
      outline: 3px solid #7bc59d;
      outline-offset: 3px;
    }

    button:disabled {
      cursor: wait;
      opacity: 0.65;
    }

    .heading,
    .detail,
    .action {
      display: block;
    }

    .heading {
      font-size: 1.25rem;
      font-weight: 650;
    }

    .detail {
      max-width: 30ch;
      margin-top: var(--space-2);
      color: var(--muted-ink);
      line-height: 1.5;
    }

    .action {
      margin-top: var(--space-5);
      color: var(--action);
      font-size: 0.9rem;
      font-weight: 650;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    'aerofoil-choice-card': ChoiceCard;
  }
}
